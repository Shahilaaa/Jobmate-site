from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from typing import Optional
from django.http import HttpRequest, HttpResponse
from typing import Optional

from .forms import LoginForm, RegisterForm, TaskRequestForm, TicketForm, WorkUpdateForm
from .forms import ProfileUpdateForm, ChatMessageForm, EmployeeProfileUpdateForm, ClientProfileUpdateForm, TestimonialForm, AccreditationForm, BankDetailForm
from .nlp_search import nlp_filter_queryset, nlp_search_text
from .models import (
    Enquiry,
    ApprovalStatus,
    ClientProfile,
    Department,
    EmployeeProfile,
    Skill,
    Payment,
    PaymentStatus,
    Profile,
    TaskRequest,
    TaskStatus,
    TicketStatus,
    UserRole,
    WorkUpdate,
    Notification,
    Conversation,
    ChatMessage,
    Testimonial,
    Accreditation,
    Portfolio,
    SupportTicket,
    FAQ,
    SupportCard,
    Project,
    ProjectApplication,
    ProjectStatus,
    ProjectApplicationStatus,
    ProjectPayment,
    BankDetail,
)


def ensure_profile(user):
    """Ensure Profile exists for a user (prevents DoesNotExist crashes)."""
    try:
        return user.profile
    except Exception:
        profile, _ = Profile.objects.get_or_create(user=user, defaults={"role": UserRole.CLIENT})
        return profile


def ensure_client(profile: Profile) -> ClientProfile:
    """Ensure ClientProfile exists for a profile."""
    client, _ = ClientProfile.objects.get_or_create(profile=profile)
    return client


def ensure_employee(profile: Profile) -> EmployeeProfile:
    """Ensure EmployeeProfile exists for a profile if role is employee."""
    emp, _ = EmployeeProfile.objects.get_or_create(profile=profile)
    return emp


def index(request: HttpRequest) -> HttpResponse:
    from django.db.models import Count as _Count
    q = (request.GET.get("q") or "").strip()

    # Departments with approved employees for the roles slider
    depts_qs = Department.objects.annotate(
        emp_count=_Count(
            "skills__employeeprofile",
            filter=Q(skills__employeeprofile__approval_status="approved"),
        )
    ).order_by("name")

    if q:
        departments = nlp_filter_queryset(q, depts_qs, lambda d: f"{d.name} {d.description}")
    else:
        departments = list(depts_qs)

    # Attach up to 6 approved employees per department (for the slider cards)
    for _dept in departments:
        _dept.approved_employees = list(
            EmployeeProfile.objects.filter(
                department=_dept, approval_status="approved"
            ).select_related("profile__user", "profile").order_by("?")[:6]
        )

    # Live stats from DB
    total_employees = EmployeeProfile.objects.filter(approval_status="approved").count()
    total_clients   = ClientProfile.objects.filter(approval_status="approved").count()
    total_tasks     = TaskRequest.objects.count()
    total_depts     = Department.objects.count()

    # Testimonials — show_on_homepage=True, up to 9, grouped into rows of 3
    _testimonials = list(
        Testimonial.objects.select_related("employee__profile__user")
        .filter(show_on_homepage=True)
        .order_by("-date")[:9]
    )
    # Split into groups of 3 for the 3-per-row slider
    testimonial_groups = [_testimonials[i:i+3] for i in range(0, len(_testimonials), 3)] if _testimonials else []

    ctx = {
        "departments":        departments,
        "total_employees":    total_employees,
        "total_clients":      total_clients,
        "total_tasks":        total_tasks,
        "total_depts":        total_depts,
        "testimonials":       _testimonials,
        "testimonial_groups": testimonial_groups,
        "q": q,
    }
    ctx["unread_count"] = (
        Notification.objects.filter(user=request.user, is_read=False).count()
        if request.user.is_authenticated
        else 0
    )
    return render(request, "pages/index.html", ctx)


def about(request: HttpRequest) -> HttpResponse:
    departments     = Department.objects.order_by("name")
    total_employees = EmployeeProfile.objects.filter(approval_status="approved").count()
    total_clients   = ClientProfile.objects.filter(approval_status="approved").count()
    total_tasks     = TaskRequest.objects.count()
    total_depts     = Department.objects.count()

    if request.method == "POST":
        name    = request.POST.get("name", "").strip()
        email   = request.POST.get("email", "").strip()
        service = request.POST.get("service", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and message:
            # ── 1. Save enquiry to database (always runs first) ──
            Enquiry.objects.create(
                name=name, email=email, service=service, message=message
            )

            # ── 2. Send email notification to jobmate393@gmail.com ──
            import logging
            _log = logging.getLogger(__name__)
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings as _settings

                service_display = service if service else "Not specified"
                subject = "New Enquiry from {} — JobMate".format(name)

                # Plain text version
                plain = (
                    "New enquiry received on JobMate.\n\n"
                    "Name:    {}\n"
                    "Email:   {}\n"
                    "Service: {}\n\n"
                    "Message:\n{}\n\n"
                    "— JobMate Enquiry System"
                ).format(name, email, service_display, message)

                # HTML version — built with .format() to avoid f-string quoting issues
                html = """<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:0;margin:0;">
<div style="max-width:560px;margin:32px auto;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1d4ed8,#1e40af);padding:28px 32px;">
    <h1 style="color:#fff;margin:0;font-size:22px;">&#128236; New Enquiry &#8212; JobMate</h1>
    <p style="color:rgba(255,255,255,.75);margin:6px 0 0;font-size:13px;">
      Received via the JobMate enquiry form
    </p>
  </div>

  <!-- Body -->
  <div style="padding:28px 32px;">
    <table style="width:100%;border-collapse:collapse;">
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;
                   font-size:13px;color:#888;width:90px;">Name</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;
                   font-size:14px;font-weight:600;color:#1a1a1a;">{name}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;
                   font-size:13px;color:#888;">Email</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;">
          <a href="mailto:{email}" style="color:#1d4ed8;">{email}</a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;
                   font-size:13px;color:#888;">Service</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;
                   font-size:14px;color:#1a1a1a;">{service}</td>
      </tr>
    </table>

    <!-- Message box -->
    <div style="margin-top:20px;background:#f8fafc;border-left:4px solid #1d4ed8;
                border-radius:4px;padding:16px 20px;">
      <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#888;
                text-transform:uppercase;letter-spacing:.5px;">Message</p>
      <p style="margin:0;font-size:14px;color:#333;line-height:1.7;">{message}</p>
    </div>

    <!-- Reply button -->
    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #f0f0f0;text-align:center;">
      <a href="mailto:{email}"
         style="display:inline-block;padding:11px 28px;background:#1d4ed8;
                color:#fff;border-radius:8px;text-decoration:none;
                font-size:13px;font-weight:700;">
        Reply to {name}
      </a>
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#f8fafc;padding:14px 32px;text-align:center;">
    <p style="margin:0;font-size:11px;color:#aaa;">
      JobMate Enquiry System &nbsp;&middot;&nbsp; Enquiry saved to database
    </p>
  </div>

</div>
</body>
</html>""".format(name=name, email=email, service=service_display, message=message)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain,
                    from_email=_settings.DEFAULT_FROM_EMAIL,
                    to=[_settings.ENQUIRY_RECIPIENT],
                    reply_to=[email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send(fail_silently=False)
                _log.info("Enquiry email sent OK → %s  (from %s <%s>)",
                          _settings.ENQUIRY_RECIPIENT, name, email)

            except Exception as _mail_err:
                _log.error(
                    "ENQUIRY EMAIL FAILED — Error: %s — "
                    "Check EMAIL_HOST_PASSWORD in .env (must be 16-char Gmail App Password)",
                    _mail_err
                )

            # ── 3. Show success & redirect (PRG pattern) ──
            messages.success(
                request,
                "Thank you {}! Your enquiry has been received. We will be in touch shortly.".format(name)
            )
            return redirect("/about/#enquire")

        else:
            messages.error(request, "Please fill in all required fields (Name, Email, Message).")
            return redirect("/about/#enquire")

    return render(request, "pages/about.html", {
        "departments":     departments,
        "total_employees": total_employees,
        "total_clients":   total_clients,
        "total_tasks":     total_tasks,
        "total_depts":     total_depts,
    })


def roles(request: HttpRequest) -> HttpResponse:
    q        = (request.GET.get("q") or "").strip()
    show_all = request.GET.get("all") == "1"

    from django.db.models import Count
    departments = Department.objects.annotate(
        emp_count=Count(
            "skills__employeeprofile",
            filter=Q(skills__employeeprofile__approval_status="approved"),
        )
    ).order_by("name")

    if q:
        # NLP search: rank departments by name + description relevance
        departments = nlp_filter_queryset(
            q,
            departments,
            lambda d: f"{d.name} {d.description}",
        )
        # nlp_filter_queryset returns a list; wrap counts/slicing accordingly
        total     = len(departments)
        has_more  = False
        show_depts = departments
    else:
        total     = departments.count()
        has_more  = (total > 9) and not show_all
        show_depts = list(departments) if show_all else list(departments[:9])

    return render(request, "pages/roles.html", {
        "departments": show_depts,
        "q": q,
        "has_more": has_more,
        "total": total,
        "show_all": show_all,
    })


def rolesinner(request: HttpRequest, employee_id: Optional[int] = None) -> HttpResponse:
    # employee_id is re-used as department_id via rolesinner_id URL
    department = None
    if employee_id:
        try:
            department = Department.objects.get(id=employee_id)
        except Department.DoesNotExist:
            # Department was deleted — show all employees instead of hard 404
            department = None

    qs = EmployeeProfile.objects.select_related(
        "profile__user", "department", "skill"
    ).filter(approval_status="approved")

    if department:
        qs = qs.filter(department=department)

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = nlp_filter_queryset(
            q,
            qs,
            lambda e: " ".join(filter(None, [
                e.profile.user.first_name,
                e.profile.user.last_name,
                e.title,
                e.skill.name if e.skill else "",
                e.department.name if e.department else "",
                e.bio,
            ]))
        )
    else:
        qs = list(qs)

    return render(request, "pages/rolesinner.html", {
        "employees": qs,
        "department": department,
        "employee_id_requested": employee_id,
        "q": q,
    })


def register(request: HttpRequest) -> HttpResponse:
    import json as _json
    from .models import Department as _Dept, Skill as _Skill

    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect(_role_redirect(user.profile))
        # form invalid — fall through to render with errors
    else:
        form = RegisterForm()

    # Build dept->skills mapping for JS-based dynamic filtering
    skills_by_dept = {}
    for sk in _Skill.objects.select_related("department").all():
        did = str(sk.department_id)   # string keys so JS select value matches
        if did not in skills_by_dept:
            skills_by_dept[did] = []
        skills_by_dept[did].append({"id": sk.id, "name": sk.name})

    return render(request, "pages/register.html", {
        "form": form,
        "skills_by_dept_json": _json.dumps(skills_by_dept),
    })


def login(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            auth_login(request, user)
            # Honour ?next= so users land back where they came from (e.g. empprofile)
            next_url = request.POST.get("next") or request.GET.get("next") or ""
            # Only allow relative internal redirects (no open-redirect)
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(_role_redirect(user.profile))
        messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()
    next_url = request.GET.get("next", "")
    return render(request, "pages/login.html", {"form": form, "next": next_url})


def admin_login(request: HttpRequest) -> HttpResponse:
    """Render the Admin Login UI and authenticate admins."""
    # If already logged in as admin, go dashboard
    if request.user.is_authenticated and is_admin(request.user):
        return redirect("dashboard_admin_dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            # Only allow admins/superusers
            if not is_admin(user):
                messages.error(request, "This account is not an admin")
            else:
                auth_login(request, user)
                return redirect("dashboard_admin_dashboard")
        else:
            messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()

    return render(request, "pages/dashboard/admin-login.html", {"form": form})


def employee_login(request: HttpRequest) -> HttpResponse:
    """Render the Employee Login UI and authenticate employees."""
    if request.user.is_authenticated and is_employee(request.user):
        return redirect("dashboard_employee_dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            if not is_employee(user):
                messages.error(request, "This account is not an employee")
            else:
                auth_login(request, user)
                return redirect("dashboard_employee_dashboard")
        else:
            messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()

    return render(request, "pages/dashboard/employeelogin.html", {"form": form})



def _compute_chart_data(task_qs, payment_qs=None, project_qs=None, proj_payment_qs=None):
    """Return daily/weekly/monthly labels + task counts + project counts + combined revenue for charts.
    Also returns per-year monthly breakdowns for the year/month selectors.
    """
    import json as _json, calendar as _cal
    from datetime import date as _date, timedelta as _td

    today = _date.today()

    # ── DAILY: last 14 days ──
    d_labels, d_tasks, d_projects, d_rev = [], [], [], []
    for i in range(13, -1, -1):
        d = today - _td(days=i)
        d_labels.append(d.strftime("%d %b"))
        d_tasks.append(task_qs.filter(created_at__date=d).count())
        d_projects.append(project_qs.filter(created_at__date=d).count() if project_qs is not None else 0)
        rev = 0
        if payment_qs is not None:
            rev = float(payment_qs.filter(task__created_at__date=d).aggregate(s=Sum("amount")).get("s") or 0)
        if proj_payment_qs is not None:
            rev += float(proj_payment_qs.filter(created_at__date=d).aggregate(s=Sum("amount")).get("s") or 0)
        d_rev.append(rev)

    # ── WEEKLY: last 12 weeks ──
    w_labels, w_tasks, w_projects, w_rev = [], [], [], []
    for i in range(11, -1, -1):
        week_end = today - _td(weeks=i)
        week_start = week_end - _td(days=6)
        w_labels.append(week_start.strftime("%d %b"))
        w_tasks.append(task_qs.filter(created_at__date__gte=week_start, created_at__date__lte=week_end).count())
        w_projects.append(project_qs.filter(created_at__date__gte=week_start, created_at__date__lte=week_end).count() if project_qs is not None else 0)
        rev = 0
        if payment_qs is not None:
            rev = float(payment_qs.filter(
                task__created_at__date__gte=week_start,
                task__created_at__date__lte=week_end
            ).aggregate(s=Sum("amount")).get("s") or 0)
        if proj_payment_qs is not None:
            rev += float(proj_payment_qs.filter(
                created_at__date__gte=week_start, created_at__date__lte=week_end
            ).aggregate(s=Sum("amount")).get("s") or 0)
        w_rev.append(rev)

    # ── MONTHLY: last 12 months (default rolling view) ──
    m_labels, m_tasks, m_projects, m_rev = [], [], [], []
    for i in range(11, -1, -1):
        yr = today.year
        mo = today.month - i
        while mo <= 0:
            mo += 12
            yr -= 1
        last_day = _cal.monthrange(yr, mo)[1]
        from datetime import date as _d2
        m_start = _d2(yr, mo, 1)
        m_end = _d2(yr, mo, last_day)
        m_labels.append(m_start.strftime("%b %Y"))
        m_tasks.append(task_qs.filter(created_at__date__gte=m_start, created_at__date__lte=m_end).count())
        m_projects.append(project_qs.filter(created_at__date__gte=m_start, created_at__date__lte=m_end).count() if project_qs is not None else 0)
        rev = 0
        if payment_qs is not None:
            rev = float(payment_qs.filter(
                task__created_at__date__gte=m_start,
                task__created_at__date__lte=m_end
            ).aggregate(s=Sum("amount")).get("s") or 0)
        if proj_payment_qs is not None:
            rev += float(proj_payment_qs.filter(
                created_at__date__gte=m_start, created_at__date__lte=m_end
            ).aggregate(s=Sum("amount")).get("s") or 0)
        m_rev.append(rev)

    # ── YEARLY: build per-year monthly data going back 5 years ──
    # yearly_data[year] = { labels:[Jan..Dec], tasks:[..], rev:[..] }
    yearly_data = {}
    start_year = today.year - 4  # last 5 years
    for yr in range(start_year, today.year + 1):
        yl, yt, yp, yr_rev = [], [], [], []
        for mo in range(1, 13):
            last_day = _cal.monthrange(yr, mo)[1]
            from datetime import date as _d2
            m_start = _d2(yr, mo, 1)
            m_end   = _d2(yr, mo, last_day)
            yl.append(_d2(yr, mo, 1).strftime("%b"))
            yt.append(task_qs.filter(created_at__date__gte=m_start, created_at__date__lte=m_end).count())
            yp.append(project_qs.filter(created_at__date__gte=m_start, created_at__date__lte=m_end).count() if project_qs is not None else 0)
            rev = 0
            if payment_qs is not None:
                rev = float(payment_qs.filter(
                    task__created_at__date__gte=m_start,
                    task__created_at__date__lte=m_end
                ).aggregate(s=Sum("amount")).get("s") or 0)
            if proj_payment_qs is not None:
                rev += float(proj_payment_qs.filter(
                    created_at__date__gte=m_start, created_at__date__lte=m_end
                ).aggregate(s=Sum("amount")).get("s") or 0)
            yr_rev.append(rev)
        yearly_data[str(yr)] = {"labels": yl, "tasks": yt, "projects": yp, "rev": yr_rev}

    available_years = list(range(start_year, today.year + 1))

    return {
        "daily_labels":    _json.dumps(d_labels),
        "daily_tasks":     _json.dumps(d_tasks),
        "daily_projects":  _json.dumps(d_projects),
        "daily_rev":       _json.dumps(d_rev),
        "weekly_labels":   _json.dumps(w_labels),
        "weekly_tasks":    _json.dumps(w_tasks),
        "weekly_projects": _json.dumps(w_projects),
        "weekly_rev":      _json.dumps(w_rev),
        "monthly_labels":   _json.dumps(m_labels),
        "monthly_tasks":    _json.dumps(m_tasks),
        "monthly_projects": _json.dumps(m_projects),
        "monthly_rev":      _json.dumps(m_rev),
        "yearly_data":      _json.dumps(yearly_data),
        "available_years":  _json.dumps(available_years),
        "current_year":     today.year,
    }

@login_required
def logout(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    return redirect("index")


def _role_redirect(profile: Profile) -> str:
    if profile.role == UserRole.ADMIN or profile.user.is_superuser:
        return "dashboard_admin_dashboard"
    if profile.role == UserRole.EMPLOYEE:
        return "dashboard_employee_dashboard"
    return "client_dashboard"  


def is_admin(user) -> bool:
    prof = ensure_profile(user)
    return bool(user.is_superuser or prof.role == UserRole.ADMIN)


def is_employee(user) -> bool:
    prof = ensure_profile(user)
    return bool(user.is_superuser or prof.role == UserRole.EMPLOYEE)
# ---------------------------
# User (Client) pages
# ---------------------------


@login_required
def employee(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    dept_id = request.GET.get("dept")
    qs = EmployeeProfile.objects.select_related("profile__user", "department", "skill").filter(approval_status="approved")

    # Filter by department if dept param is provided
    active_department = None
    if dept_id:
        try:
            active_department = Department.objects.get(id=dept_id)
            qs = qs.filter(department=active_department)
        except Department.DoesNotExist:
            active_department = None

    employees = nlp_filter_queryset(
        q,
        qs,
        lambda e: " ".join(filter(None, [
            e.profile.user.first_name,
            e.profile.user.last_name,
            e.title,
            e.skill.name if e.skill else "",
            e.department.name if e.department else "",
            e.bio,
        ]))
    ) if q else list(qs)
    unread = Notification.objects.filter(user=request.user, is_read=False).count() if request.user.is_authenticated else 0
    return render(request, "pages/employee.html", {
        "employees": employees,
        "q": q,
        "unread_count": unread,
        "active_department": active_department,
    })


@login_required
def client_dashboard(request):
    """Client main dashboard — tasks, projects, stats, charts."""
    import json as _json
    from datetime import date as _date, timedelta as _td

    profile = ensure_profile(request.user)
    if profile.role not in (UserRole.CLIENT,) and not request.user.is_superuser:
        return redirect(_role_redirect(profile))

    client = ensure_client(profile)

    # Task querysets
    tasks_qs    = TaskRequest.objects.filter(client=client).select_related("employee__profile__user").order_by("-created_at")
    payment_qs  = Payment.objects.filter(task__client=client)

    # Project querysets
    projects_qs   = Project.objects.filter(client=client).order_by("-created_at")
    proj_pay_qs   = ProjectPayment.objects.filter(client=client)

    # Stats
    task_total     = tasks_qs.count()
    task_active    = tasks_qs.filter(status__in=[TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS]).count()
    task_completed = tasks_qs.filter(status=TaskStatus.COMPLETED).count()
    task_pending   = tasks_qs.filter(status=TaskStatus.PENDING).count()
    task_spent     = float(payment_qs.filter(status=PaymentStatus.PAID).aggregate(s=Sum("amount")).get("s") or 0)

    proj_total     = projects_qs.count()
    proj_active    = projects_qs.filter(status__in=["active","assigned","work_submitted"]).count()
    proj_completed = projects_qs.filter(status="completed").count()
    proj_spent     = float(proj_pay_qs.filter(status=PaymentStatus.PAID).aggregate(s=Sum("amount")).get("s") or 0)

    stats = {
        "task_total":     task_total,
        "task_active":    task_active,
        "task_completed": task_completed,
        "task_pending":   task_pending,
        "proj_total":     proj_total,
        "proj_active":    proj_active,
        "proj_completed": proj_completed,
        "task_spent":     task_spent,
        "proj_spent":     proj_spent,
        "total_spent":    task_spent + proj_spent,
    }

    status_labels = ["Pending", "Active", "Submitted", "Completed", "Rejected"]
    status_data   = [
        task_pending, task_active,
        tasks_qs.filter(status=TaskStatus.SUBMITTED).count(),
        task_completed,
        tasks_qs.filter(status=TaskStatus.REJECTED).count(),
    ]

    # Project status breakdown for client
    proj_status_labels = ["Active", "Assigned", "Work Submitted", "Completed", "Closed"]
    proj_status_data   = [
        projects_qs.filter(status="active").count(),
        projects_qs.filter(status="assigned").count(),
        projects_qs.filter(status="work_submitted").count(),
        projects_qs.filter(status="completed").count(),
        projects_qs.filter(status="closed").count(),
    ]

    chart_ctx = _compute_chart_data(tasks_qs, payment_qs, projects_qs, proj_pay_qs)

    q = (request.GET.get("q") or "").strip()
    tasks_show = nlp_filter_queryset(
        q, tasks_qs,
        lambda t: f"{t.title} {t.employee.profile.user.get_full_name() if t.employee else ''} {t.description}"
    ) if q else list(tasks_qs[:10])

    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, "pages/client-dashboard.html", {
        "stats":          stats,
        "tasks":          tasks_show[:10],
        "projects":       projects_qs[:8],
        "q":              q,
        "unread_count":   unread,
        "status_labels":       _json.dumps(status_labels),
        "status_data":         _json.dumps(status_data),
        "proj_status_labels":  _json.dumps(proj_status_labels),
        "proj_status_data":    _json.dumps(proj_status_data),
        **chart_ctx,
    })


@login_required
def works(request: HttpRequest) -> HttpResponse:
    if request.user.profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(request.user.profile))
    client = ensure_client(ensure_profile(request.user))

    # Handle mark-complete POST from works list page
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        action  = request.POST.get("action")
        if task_id and action == "mark_complete":
            task_obj = get_object_or_404(TaskRequest, id=task_id, client=client)
            if task_obj.status == TaskStatus.SUBMITTED:
                task_obj.status = TaskStatus.COMPLETED
                task_obj.save()
                if not Payment.objects.filter(task=task_obj).exists():
                    # Always compute: total_hours × hourly_rate
                    _hours = task_obj.total_hours or 0
                    _rate  = task_obj.employee.hourly_rate or 0
                    amount = float(_hours) * float(_rate) if _hours and _rate else float(task_obj.estimated_cost or 0)
                    Payment.objects.create(
                        task=task_obj, client=client,
                        amount=amount, status=PaymentStatus.PENDING,
                    )
                Notification.objects.create(
                    user=task_obj.employee.profile.user,
                    title="Task marked as completed",
                    message=f"{request.user.get_full_name() or request.user.username} has marked '{task_obj.title}' as completed. Great work!",
                    link=f"/employee_app/task-detail/{task_obj.id}/",
                )
                messages.success(request, f"'{task_obj.title}' has been marked as completed!")
        return redirect("works")

    q = (request.GET.get("q") or "").strip()
    tasks = TaskRequest.objects.filter(client=client).select_related(
        "employee__profile__user"
    ).prefetch_related("work_updates").order_by("-created_at")
    filter_by = request.GET.get("filter", "all")
    if filter_by == "ongoing":
        tasks = tasks.filter(status__in=[TaskStatus.PENDING, TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS, TaskStatus.SUBMITTED])
    elif filter_by == "completed":
        tasks = tasks.filter(status=TaskStatus.COMPLETED)
    tasks = nlp_filter_queryset(
        q, tasks,
        lambda t: " ".join(filter(None, [
            t.title, t.description,
            t.employee.profile.user.get_full_name() if t.employee else "",
            t.status,
        ]))
    ) if q else list(tasks)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/works.html", {"tasks": tasks, "filter": filter_by, "q": q, "unread_count": unread})


@login_required
def worksinner(request: HttpRequest, task_id: Optional[int] = None) -> HttpResponse:
    if request.user.profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(request.user.profile))
    client = ensure_client(ensure_profile(request.user))
    task = None
    if task_id:
        task = get_object_or_404(
            TaskRequest.objects.select_related("employee__profile__user", "employee__department", "employee__skill"),
            id=task_id, client=client
        )
    else:
        task = TaskRequest.objects.filter(client=client).select_related(
            "employee__profile__user", "employee__department", "employee__skill"
        ).order_by("-created_at").first()

    # Handle client marking task as complete
    if request.method == "POST" and task:
        action = request.POST.get("action")
        if action == "mark_complete" and task.status == TaskStatus.SUBMITTED:
            task.status = TaskStatus.COMPLETED
            task.save()
            # Auto-create payment
            if not Payment.objects.filter(task=task).exists():
                _hours = task.total_hours or 0
                _rate  = task.employee.hourly_rate or 0
                amount = float(_hours) * float(_rate) if _hours and _rate else float(task.estimated_cost or 0)
                Payment.objects.create(
                    task=task,
                    client=task.client,
                    amount=amount,
                    status=PaymentStatus.PENDING,
                )
            # Notify employee
            Notification.objects.create(
                user=task.employee.profile.user,
                title="Task marked as completed",
                message=f"{request.user.get_full_name() or request.user.username} has marked '{task.title}' as completed. Great work!",
                link=f"/employee_app/task-detail/{task.id}/",
            )
            messages.success(request, "Task has been marked as completed. Thank you!")
            return redirect("worksinner_id", task_id=task.id)
        elif action == "mark_complete":
            messages.error(request, "Task can only be marked complete after the employee has submitted their work.")

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/worksinner.html", {"task": task, "unread_count": unread})


@login_required
def task(request: HttpRequest) -> HttpResponse:
    profile = ensure_profile(request.user)

    # Only CLIENT can create task requests from user_app pages.
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))

    client = ensure_client(profile)

    initial = {}
    emp_prefill = request.GET.get("employee")
    if emp_prefill and emp_prefill.isdigit():
        initial["employee"] = int(emp_prefill)

    if request.method == "POST":
        form = TaskRequestForm(request.POST)
        if form.is_valid():
            task_obj: TaskRequest = form.save(commit=False)
            task_obj.client = client
            task_obj.status = TaskStatus.PENDING
            # Budget stores hourly_rate for reference only — actual amount is hours × rate
            task_obj.budget = task_obj.employee.hourly_rate or 0
            task_obj.save()
            Notification.objects.create(
                user=task_obj.employee.profile.user,
                title="New task request",
                message=f"{request.user.get_full_name() or request.user.username} requested: {task_obj.title}",
                link="/employee_app/task-request/",
            )
            messages.success(request, "Task request submitted")
            return redirect("works")
        messages.error(request, "Please fix the errors below")
    else:
        form = TaskRequestForm(initial=initial)

    import json as _json
    q_emp = (request.GET.get("q") or "").strip()
    employees_qs = EmployeeProfile.objects.select_related(
        "profile__user", "department", "skill"
    ).filter(approval_status="approved")
    # Apply NLP search on employees if query provided
    if q_emp:
        employees_qs = nlp_filter_queryset(
            q_emp, employees_qs,
            lambda e: " ".join(filter(None, [
                e.profile.user.get_full_name() or e.profile.user.username,
                e.title, e.bio,
                e.skill.name if e.skill else "",
                e.department.name if e.department else "",
            ]))
        )
    else:
        employees_qs = list(employees_qs)
    # Build employee list with dept/skill/hourly_rate for JS display
    emp_list = []
    for e in employees_qs:
        emp_list.append({
            "id": e.id,
            "name": e.profile.user.get_full_name() or e.profile.user.username,
            "dept": e.department.name if e.department else "",
            "skill": e.skill.name if e.skill else "",
            "title": e.title or "",
            "hourly_rate": float(e.hourly_rate or 0),
        })
    return render(request, "pages/task.html", {
        "form": form,
        "emp_list_json": _json.dumps(emp_list),
        "prefill_employee": emp_prefill or "",
        "q": q_emp,
    })


@login_required
def task_edit(request: HttpRequest, task_id: int) -> HttpResponse:
    """Client can edit a PENDING task (before employee accepts)."""
    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))
    client = ensure_client(profile)
    task_obj = get_object_or_404(TaskRequest, id=task_id, client=client, status=TaskStatus.PENDING)

    import json as _json
    employees_qs = EmployeeProfile.objects.select_related(
        "profile__user", "department", "skill"
    ).filter(approval_status="approved")
    emp_list = []
    for e in employees_qs:
        emp_list.append({
            "id": e.id,
            "name": e.profile.user.get_full_name() or e.profile.user.username,
            "dept": e.department.name if e.department else "",
            "skill": e.skill.name if e.skill else "",
            "hourly_rate": float(e.hourly_rate or 0),
        })

    if request.method == "POST":
        form = TaskRequestForm(request.POST, instance=task_obj)
        if form.is_valid():
            updated = form.save(commit=False)
            # Keep budget as hourly_rate reference
            updated.budget = updated.employee.hourly_rate or 0
            updated.save()
            messages.success(request, "Task updated successfully.")
            return redirect("works")
        messages.error(request, "Please fix the errors below.")
    else:
        form = TaskRequestForm(instance=task_obj)

    return render(request, "pages/task.html", {
        "form": form,
        "emp_list_json": _json.dumps(emp_list),
        "prefill_employee": str(task_obj.employee_id),
        "edit_mode": True,
        "task_obj": task_obj,
    })


@login_required
def task_delete(request: HttpRequest, task_id: int) -> HttpResponse:
    """Client can delete a PENDING task (before employee accepts)."""
    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))
    client = ensure_client(profile)
    task_obj = get_object_or_404(TaskRequest, id=task_id, client=client, status=TaskStatus.PENDING)
    if request.method == "POST":
        title = task_obj.title
        task_obj.delete()
        messages.success(request, f"Task '{title}' deleted.")
    return redirect("works")


@login_required
def payments(request: HttpRequest) -> HttpResponse:
    if request.user.profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(request.user.profile))
    client = ensure_client(ensure_profile(request.user))
    q = (request.GET.get("q") or "").strip()

    # Task payments
    payments_qs = Payment.objects.filter(client=client).select_related(
        "task", "task__employee__profile__user", "task__employee"
    ).order_by("-id")
    payments_list = nlp_filter_queryset(
        q, payments_qs,
        lambda p: " ".join(filter(None, [
            p.task.title if p.task else "",
            p.task.employee.profile.user.get_full_name() if p.task and p.task.employee else "",
            p.status, p.method, str(p.amount),
        ]))
    ) if q else list(payments_qs)

    # Project payments
    proj_payments_qs = ProjectPayment.objects.filter(client=client).select_related(
        "project", "employee__profile__user"
    ).order_by("-created_at")
    proj_payments_list = nlp_filter_queryset(
        q, proj_payments_qs,
        lambda pp: " ".join(filter(None, [
            pp.project.title,
            pp.employee.profile.user.get_full_name() if pp.employee else "",
            pp.status, pp.method, str(pp.amount),
        ]))
    ) if q else list(proj_payments_qs)

    # Summary totals
    task_total    = sum(float(p.amount) for p in payments_list)
    task_paid     = sum(float(p.amount) for p in payments_list if p.status == "paid")
    task_pending  = sum(float(p.amount) for p in payments_list if p.status != "paid")
    proj_total    = sum(float(pp.amount) for pp in proj_payments_list)
    proj_paid     = sum(float(pp.amount) for pp in proj_payments_list if pp.status == "paid")
    proj_pending  = sum(float(pp.amount) for pp in proj_payments_list if pp.status != "paid")
    grand_total   = task_total + proj_total

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/payments.html", {
        "payments":          payments_list,
        "proj_payments":     proj_payments_list,
        "task_total":        task_total,
        "task_paid":         task_paid,
        "task_pending":      task_pending,
        "proj_total":        proj_total,
        "proj_paid":         proj_paid,
        "proj_pending":      proj_pending,
        "grand_total":       grand_total,
        "q":                 q,
        "unread_count":      unread,
    })


@login_required
@login_required
def payment_gateway(request, payment_id):
    """Razorpay payment gateway — client pays for a completed task."""
    from django.conf import settings as djsettings
    from django.http import JsonResponse as _JR
    import razorpay, hmac, hashlib

    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))

    client  = ensure_client(profile)
    payment = get_object_or_404(
        Payment.objects.select_related("task__employee__profile__user", "task__employee"),
        id=payment_id, client=client
    )

    if payment.status == PaymentStatus.PAID:
        messages.info(request, "This payment has already been processed.")
        return redirect("payments")

    rzp = razorpay.Client(auth=(djsettings.RAZORPAY_KEY_ID, djsettings.RAZORPAY_KEY_SECRET))

    # ── Create Razorpay order ────────────────────────────────────────────────
    if request.method == "POST" and request.POST.get("action") == "create_order":
        amount_paise = int(float(payment.amount) * 100)
        order_data = {
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  f"task_{payment.id}",
            "notes":    {
                "task":          payment.task.title,
                "client":        request.user.email,
                "payment_db_id": str(payment.id),
            },
        }
        try:
            order = rzp.order.create(data=order_data)
            payment.razorpay_order_id = order["id"]
            payment.save(update_fields=["razorpay_order_id"])
            return _JR({"order_id": order["id"], "amount": amount_paise,
                        "currency": "INR", "key": djsettings.RAZORPAY_KEY_ID})
        except Exception as e:
            err = str(e)
            # Network / proxy / API error - return JSON so JS shows proper message
            return _JR({"error": True,
                        "message": f"Razorpay API error: {err[:120]}. Check your internet connection and API keys."
                       }, status=200)

    # ── Verify signature + mark paid ─────────────────────────────────────────
    if request.method == "POST" and request.POST.get("razorpay_payment_id"):
        rzp_payment_id  = request.POST.get("razorpay_payment_id", "")
        rzp_order_id    = request.POST.get("razorpay_order_id", "")
        rzp_signature   = request.POST.get("razorpay_signature", "")
        try:
            rzp.utility.verify_payment_signature({
                "razorpay_order_id":   rzp_order_id,
                "razorpay_payment_id": rzp_payment_id,
                "razorpay_signature":  rzp_signature,
            })
            payment.status              = PaymentStatus.PAID
            payment.method              = "razorpay"
            payment.transaction_id      = rzp_payment_id
            payment.razorpay_payment_id = rzp_payment_id
            payment.razorpay_signature  = rzp_signature
            payment.paid_at             = timezone.now()
            payment.save()
            # Notify employee
            Notification.objects.create(
                user=payment.task.employee.profile.user,
                title="Payment received via Razorpay",
                message=(f"₹{payment.employee_payout} credited for task '{payment.task.title}'. "
                         f"Admin commission: ₹{payment.admin_commission}."),
                link=f"/employee_app/task-detail/{payment.task_id}/",
            )
            messages.success(request,
                f"✅ Payment of ₹{payment.amount} successful! "
                f"Employee receives ₹{payment.employee_payout} (after 20% admin commission).")
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "❌ Payment verification failed. Please contact support.")
        return redirect("payments")

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/payment_gateway.html", {
        "payment":     payment,
        "is_project":  False,
        "unread_count": unread,
        "admin_cut":   round(float(payment.amount) * 0.20, 2),
        "emp_cut":     round(float(payment.amount) * 0.80, 2),
        "razorpay_key": djsettings.RAZORPAY_KEY_ID,
    })


@login_required
def project_payment_gateway(request, payment_id):
    """Razorpay payment gateway — client pays for a completed project."""
    from django.conf import settings as djsettings
    from django.http import JsonResponse as _JR
    import razorpay

    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))

    client  = ensure_client(profile)
    payment = get_object_or_404(
        ProjectPayment.objects.select_related("project", "employee__profile__user"),
        id=payment_id, client=client
    )

    if payment.status == PaymentStatus.PAID:
        messages.info(request, "This payment has already been processed.")
        return redirect("client_projects")

    rzp = razorpay.Client(auth=(djsettings.RAZORPAY_KEY_ID, djsettings.RAZORPAY_KEY_SECRET))

    if request.method == "POST" and request.POST.get("action") == "create_order":
        amount_paise = int(float(payment.amount) * 100)
        order_data = {
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  f"proj_{payment.id}",
            "notes":    {"project": payment.project.title, "client": request.user.email},
        }
        order = rzp.order.create(data=order_data)
        payment.razorpay_order_id = order["id"]
        payment.save(update_fields=["razorpay_order_id"])
        return _JR({"order_id": order["id"], "amount": amount_paise,
                    "currency": "INR", "key": djsettings.RAZORPAY_KEY_ID})

    if request.method == "POST" and request.POST.get("razorpay_payment_id"):
        rzp_payment_id = request.POST.get("razorpay_payment_id", "")
        rzp_order_id   = request.POST.get("razorpay_order_id", "")
        rzp_signature  = request.POST.get("razorpay_signature", "")
        try:
            rzp.utility.verify_payment_signature({
                "razorpay_order_id":   rzp_order_id,
                "razorpay_payment_id": rzp_payment_id,
                "razorpay_signature":  rzp_signature,
            })
            payment.status              = PaymentStatus.PAID
            payment.method              = "razorpay"
            payment.transaction_id      = rzp_payment_id
            payment.razorpay_payment_id = rzp_payment_id
            payment.razorpay_signature  = rzp_signature
            payment.save()
            Notification.objects.create(
                user=payment.employee.profile.user,
                title="Project payment received via Razorpay",
                message=(f"₹{payment.employee_payout} credited for project '{payment.project.title}'. "
                         f"Admin commission: ₹{payment.admin_commission}."),
                link="/employee_app/employee-projects/",
            )
            messages.success(request,
                f"✅ Project payment of ₹{payment.amount} successful! "
                f"Employee receives ₹{payment.employee_payout}.")
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "❌ Payment verification failed.")
        return redirect("client_projects")

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/payment_gateway.html", {
        "payment":     payment,
        "is_project":  True,
        "unread_count": unread,
        "admin_cut":   round(float(payment.amount) * 0.20, 2),
        "emp_cut":     round(float(payment.amount) * 0.80, 2),
        "razorpay_key": djsettings.RAZORPAY_KEY_ID,
    })


from django.http import JsonResponse

def support_submit_ticket(request):
    """AJAX POST — submit a new support ticket, saves to DB and emails admin."""
    import logging
    _log = logging.getLogger(__name__)

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Login required."}, status=401)
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    subject = (request.POST.get("subject") or "").strip()
    message = (request.POST.get("message") or "").strip()
    if not subject:
        return JsonResponse({"ok": False, "error": "Subject is required."})
    if not message:
        return JsonResponse({"ok": False, "error": "Message is required."})

    # ── 1. Save ticket to database ──────────────────────────────────────────
    ticket = SupportTicket.objects.create(
        created_by=request.user,
        subject=subject,
        message=message,
        status=TicketStatus.OPEN,
    )

    # ── 2. Send email notification to admin ─────────────────────────────────
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings as _settings

        user        = request.user
        full_name   = user.get_full_name() or user.username
        user_email  = user.email or "no-email@jobmate.com"
        ticket_id   = ticket.id
        created_str = "{} {} {}".format(
            ticket.created_at.day,
            ticket.created_at.strftime("%b"),
            ticket.created_at.year,
        )

        email_subject = "Support Ticket #{} — {} — JobMate".format(ticket_id, subject[:60])

        plain = (
            "New support ticket submitted on JobMate.\n\n"
            "Ticket ID : #{}\n"
            "Client    : {} ({})\n"
            "Subject   : {}\n"
            "Submitted : {}\n\n"
            "Message:\n{}\n\n"
            "— JobMate Support System"
        ).format(ticket_id, full_name, user_email, subject, created_str, message)

        html = """<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:0;margin:0;">
<div style="max-width:580px;margin:32px auto;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1d4ed8,#1e40af);padding:28px 32px;">
    <h1 style="color:#fff;margin:0;font-size:22px;">&#127915; New Support Ticket &#8212; JobMate</h1>
    <p style="color:rgba(255,255,255,.75);margin:6px 0 0;font-size:13px;">
      Ticket #{ticket_id} &nbsp;&bull;&nbsp; {created_str}
    </p>
  </div>

  <!-- Body -->
  <div style="padding:28px 32px;">
    <table style="width:100%;border-collapse:collapse;">
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#888;width:100px;">Ticket ID</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;font-weight:700;color:#1d4ed8;">#{ticket_id}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#888;">Client</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;font-weight:600;color:#1a1a1a;">{full_name}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#888;">Email</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;">
          <a href="mailto:{user_email}" style="color:#1d4ed8;">{user_email}</a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#888;">Subject</td>
        <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:14px;font-weight:600;color:#1a1a1a;">{subject}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;font-size:13px;color:#888;">Status</td>
        <td style="padding:10px 0;font-size:14px;">
          <span style="background:#fef3c7;color:#92400e;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;">Open</span>
        </td>
      </tr>
    </table>

    <!-- Message -->
    <div style="margin-top:20px;background:#f8fafc;border-left:4px solid #1d4ed8;
                border-radius:4px;padding:16px 20px;">
      <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#888;
                text-transform:uppercase;letter-spacing:.5px;">Message</p>
      <p style="margin:0;font-size:14px;color:#333;line-height:1.7;">{message}</p>
    </div>

    <!-- Reply button -->
    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #f0f0f0;text-align:center;">
      <a href="mailto:{user_email}?subject=Re: Support Ticket #{ticket_id} — {subject}"
         style="display:inline-block;padding:11px 28px;background:#1d4ed8;
                color:#fff;border-radius:8px;text-decoration:none;
                font-size:13px;font-weight:700;margin-right:8px;">
        &#9993; Reply to Client
      </a>
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#f8fafc;padding:14px 32px;text-align:center;">
    <p style="margin:0;font-size:11px;color:#aaa;">
      JobMate Support System &nbsp;&middot;&nbsp; Ticket #{ticket_id} saved to database
    </p>
  </div>
</div>
</body>
</html>""".format(
            ticket_id=ticket_id,
            full_name=full_name,
            user_email=user_email,
            subject=subject,
            message=message.replace("\n", "<br>"),
            created_str=created_str,
        )

        msg = EmailMultiAlternatives(
            subject=email_subject,
            body=plain,
            from_email=_settings.DEFAULT_FROM_EMAIL,
            to=[_settings.ENQUIRY_RECIPIENT],
            reply_to=[user_email],
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        _log.info("Support ticket #%s email sent → %s", ticket_id, _settings.ENQUIRY_RECIPIENT)

    except Exception as _mail_err:
        _log.error("SUPPORT TICKET EMAIL FAILED — Ticket #%s — Error: %s", ticket.id, _mail_err)
        # Email failure does NOT block the ticket from being saved — DB save already done above

    # ── 3. Return success ───────────────────────────────────────────────────
    return JsonResponse({
        "ok": True,
        "ticket": {
            "id": ticket.id,
            "subject": ticket.subject,
            "message": ticket.message,
            "status": ticket.status,
            "status_display": ticket.get_status_display(),
            "created_at": "{} {} {}".format(ticket.created_at.day, ticket.created_at.strftime("%b"), ticket.created_at.year),
        }
    })


def support_tickets_json(request):
    """AJAX GET — returns all tickets for the current user as JSON."""
    if not request.user.is_authenticated:
        return JsonResponse({"tickets": []}, status=401)
    tickets = SupportTicket.objects.filter(created_by=request.user).order_by("-created_at")
    data = [{
        "id": t.id,
        "subject": t.subject,
        "message": t.message[:120] + ("…" if len(t.message) > 120 else ""),
        "status": t.status,
        "status_display": t.get_status_display(),
        "created_at": "{} {} {}".format(t.created_at.day, t.created_at.strftime("%b"), t.created_at.year),
    } for t in tickets]
    return JsonResponse({"tickets": data})



@login_required
def support(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    faqs_qs = FAQ.objects.filter(is_active=True)
    faqs = nlp_filter_queryset(
        q, faqs_qs,
        lambda f: f"{f.question} {f.answer}"
    ) if q else list(faqs_qs)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    support_cards = SupportCard.objects.filter(is_active=True)[:3]
    return render(request, "pages/support.html", {
        "faqs": faqs, "q": q, "unread_count": unread,
        "support_cards": support_cards,
    })


@login_required
def dashboard_admin_support(request: HttpRequest) -> HttpResponse:
    """Admin view — list all support tickets, filter by status."""
    if not is_admin(request.user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Admin access required.")
    status_filter = request.GET.get("status", "all")
    qs = SupportTicket.objects.select_related("created_by").order_by("-created_at")
    if status_filter in ("open", "in_progress", "closed"):
        qs = qs.filter(status=status_filter)
    tickets = list(qs)
    counts = {
        "all":         SupportTicket.objects.count(),
        "open":        SupportTicket.objects.filter(status=TicketStatus.OPEN).count(),
        "in_progress": SupportTicket.objects.filter(status=TicketStatus.IN_PROGRESS).count(),
        "closed":      SupportTicket.objects.filter(status=TicketStatus.CLOSED).count(),
    }
    current_user_avatar_url = None
    try:
        prof = request.user.userprofile
        if prof.avatar:
            current_user_avatar_url = prof.avatar.url
    except Exception:
        pass
    return render(request, "pages/dashboard/admin-support.html", {
        "tickets": tickets,
        "counts": counts,
        "status_filter": status_filter,
        "current_user_avatar_url": current_user_avatar_url,
        "current_user_initials": (request.user.first_name[:1] + request.user.last_name[:1]).upper() or request.user.username[:2].upper(),
    })


@login_required
def dashboard_admin_support_update(request: HttpRequest, pk: int) -> "JsonResponse":
    """AJAX POST — update ticket status or send reply email."""
    import logging
    _log = logging.getLogger(__name__)
    if not is_admin(request.user):
        return JsonResponse({"ok": False, "error": "Admin only."}, status=403)
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required."}, status=405)
    try:
        ticket = SupportTicket.objects.select_related("created_by").get(pk=pk)
    except SupportTicket.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Ticket not found."}, status=404)

    new_status = (request.POST.get("status") or "").strip()
    reply_msg  = (request.POST.get("reply") or "").strip()

    # Update status if provided
    if new_status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED):
        ticket.status = new_status
        ticket.save()

    # Send reply email if message provided
    if reply_msg:
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings as _settings

            client_email = ticket.created_by.email or ""
            client_name  = ticket.created_by.get_full_name() or ticket.created_by.username

            if client_email:
                email_subject = "Re: Support Ticket #{} — {}".format(ticket.id, ticket.subject[:60])
                plain = (
                    "Hi {},\n\n"
                    "Our support team has replied to your ticket #{}.\n\n"
                    "Your original message:\n{}\n\n"
                    "Our reply:\n{}\n\n"
                    "Ticket status: {}\n\n"
                    "— JobMate Support Team"
                ).format(client_name, ticket.id, ticket.message, reply_msg, ticket.get_status_display())

                status_color = {"open": "#f59e0b", "in_progress": "#3b82f6", "closed": "#10b981"}.get(ticket.status, "#6b7280")
                html = """<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:0;margin:0;">
<div style="max-width:580px;margin:32px auto;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1);">
  <div style="background:linear-gradient(135deg,#1d4ed8,#1e40af);padding:28px 32px;">
    <h1 style="color:#fff;margin:0;font-size:22px;">&#127915; Support Reply &#8212; JobMate</h1>
    <p style="color:rgba(255,255,255,.75);margin:6px 0 0;font-size:13px;">Ticket #{ticket_id}</p>
  </div>
  <div style="padding:28px 32px;">
    <p style="font-size:15px;color:#333;">Hi <strong>{client_name}</strong>,</p>
    <p style="font-size:14px;color:#555;">Our support team has replied to your ticket.</p>
    <div style="margin:20px 0;background:#f8fafc;border-left:4px solid #6b7280;border-radius:4px;padding:14px 18px;">
      <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;">Your original message</p>
      <p style="margin:0;font-size:13px;color:#777;line-height:1.6;">{original_msg}</p>
    </div>
    <div style="margin:20px 0;background:#eff6ff;border-left:4px solid #1d4ed8;border-radius:4px;padding:14px 18px;">
      <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;">Support Reply</p>
      <p style="margin:0;font-size:14px;color:#1a1a1a;line-height:1.7;">{reply_msg}</p>
    </div>
    <p style="font-size:13px;color:#888;">Ticket status: <span style="background:{status_color};color:#fff;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;">{status_display}</span></p>
  </div>
  <div style="background:#f8fafc;padding:14px 32px;text-align:center;">
    <p style="margin:0;font-size:11px;color:#aaa;">JobMate Support System &nbsp;&middot;&nbsp; Ticket #{ticket_id}</p>
  </div>
</div>
</body>
</html>""".format(
                    ticket_id=ticket.id,
                    client_name=client_name,
                    original_msg=ticket.message.replace("\n", "<br>"),
                    reply_msg=reply_msg.replace("\n", "<br>"),
                    status_color=status_color,
                    status_display=ticket.get_status_display(),
                )
                msg = EmailMultiAlternatives(
                    subject=email_subject,
                    body=plain,
                    from_email=_settings.DEFAULT_FROM_EMAIL,
                    to=[client_email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send(fail_silently=False)
                _log.info("Reply email sent for ticket #%s → %s", ticket.id, client_email)
                return JsonResponse({"ok": True, "status": ticket.status, "email_sent": True})
            else:
                return JsonResponse({"ok": True, "status": ticket.status, "email_sent": False, "note": "Client has no email address."})
        except Exception as e:
            _log.error("Reply email failed for ticket #%s: %s", ticket.id, e)
            return JsonResponse({"ok": True, "status": ticket.status, "email_sent": False, "note": str(e)})

    return JsonResponse({"ok": True, "status": ticket.status, "email_sent": False})


@login_required
def myprofile(request: HttpRequest) -> HttpResponse:
    profile = ensure_profile(request.user)

    # Ensure role containers exist so other pages don't crash.
    if profile.role == UserRole.CLIENT:
        ensure_client(profile)
    elif profile.role == UserRole.EMPLOYEE:
        ensure_employee(profile)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=profile, user=request.user)
        # Handle employee-specific update
        if profile.role == UserRole.EMPLOYEE:
            emp_profile = ensure_employee(profile)
            eform = EmployeeProfileUpdateForm(request.POST, request.FILES, instance=emp_profile)
            cform = None
            if form.is_valid() and eform.is_valid():
                form.save()
                eform.save()
                messages.success(request, "Profile updated")
                return redirect("myprofile")
        else:
            client_profile = ensure_client(profile)
            cform = ClientProfileUpdateForm(request.POST, request.FILES, instance=client_profile)
            eform = None
            if form.is_valid() and cform.is_valid():
                form.save()
                cform.save()
                messages.success(request, "Profile updated")
                return redirect("myprofile")
        messages.error(request, "Please fix the errors")
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)
        if profile.role == UserRole.EMPLOYEE:
            emp_profile = ensure_employee(profile)
            eform = EmployeeProfileUpdateForm(instance=emp_profile)
            cform = None
        else:
            client_profile = ensure_client(profile)
            cform = ClientProfileUpdateForm(instance=client_profile)
            eform = None

    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    # Chart data for user dashboard
    import json as _json
    client_tasks_qs = TaskRequest.objects.filter(client__profile__user=request.user)
    client_payments_qs = Payment.objects.filter(client__profile__user=request.user)
    chart_ctx = _compute_chart_data(client_tasks_qs, client_payments_qs)

    # Status breakdown for client
    usr_tasks = client_tasks_qs
    usr_status_labels = ["Pending", "Active", "Submitted", "Completed", "Rejected"]
    usr_status_data = [
        usr_tasks.filter(status=TaskStatus.PENDING).count(),
        usr_tasks.filter(status__in=[TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS]).count(),
        usr_tasks.filter(status=TaskStatus.SUBMITTED).count(),
        usr_tasks.filter(status=TaskStatus.COMPLETED).count(),
        usr_tasks.filter(status=TaskStatus.REJECTED).count(),
    ]

    return render(request, "pages/myprofile.html", {
        "form": form,
        "pform": form,
        "cform": cform,
        "eform": eform,
        "unread_count": unread,
        "status_labels": _json.dumps(usr_status_labels),
        "status_data": _json.dumps(usr_status_data),
        **chart_ctx,
    })


@login_required
def empprofile(request: HttpRequest, employee_id: Optional[int] = None) -> HttpResponse:
    """Employee public profile — login required. Supports /empprofile/<id>/ and ?employee=<id>."""
    if employee_id is None:
        qp = request.GET.get("employee") or request.GET.get("employee_id")
        if qp:
            try:
                employee_id = int(qp)
            except (ValueError, TypeError):
                employee_id = None

    qs = EmployeeProfile.objects.select_related(
        "profile__user", "department", "skill"
    ).filter(approval_status="approved")

    if employee_id:
        employee = get_object_or_404(qs, id=employee_id)
    else:
        return redirect("roles")

    portfolio_items = employee.portfolio_items.all()
    testimonials    = employee.testimonials.all()
    accreditations  = employee.accreditations.all()

    back_url = f"/rolesinner/{employee.department_id}/" if employee.department_id else "/rolesinner/"

    return render(request, "pages/empprofile.html", {
        "employee":        employee,
        "portfolio_items": portfolio_items,
        "testimonials":    testimonials,
        "accreditations":  accreditations,
        "back_url":        back_url,
    })



# ---------------------------
# Employee dashboard
# ---------------------------


@login_required
def dashboard_employee_dashboard(request: HttpRequest) -> HttpResponse:
    import json as _json
    from datetime import date as _date, timedelta as _td

    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    tasks = (
        TaskRequest.objects.filter(employee=emp)
        .select_related("client__profile__user")
        .order_by("-created_at")
    )

    # Project querysets for this employee - show assigned + accepted applications
    from django.db.models import Q as _Q
    projects = Project.objects.filter(
        Q(assigned_to=emp) |
        Q(applications__employee=emp, applications__status="accepted")
    ).distinct().order_by("-created_at")
    proj_payments = ProjectPayment.objects.filter(employee=emp)

    # Task stats
    task_total      = tasks.count()
    task_completed  = tasks.filter(status=TaskStatus.COMPLETED).count()
    task_pending    = tasks.filter(status=TaskStatus.PENDING).count()
    task_active     = tasks.filter(status__in=[TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS]).count()
    task_submitted  = tasks.filter(status=TaskStatus.SUBMITTED).count()
    task_rejected   = tasks.filter(status=TaskStatus.REJECTED).count()
    task_revenue    = float(Payment.objects.filter(task__employee=emp, status=PaymentStatus.PAID).aggregate(s=Sum("employee_payout")).get("s") or 0)

    # Project stats
    proj_total      = Project.objects.filter(
        applications__employee=emp,
        applications__status="accepted"
    ).count()
    proj_active     = projects.filter(status__in=["active","assigned","work_submitted"]).count()
    proj_completed  = projects.filter(status="completed").count()
    proj_revenue    = float(proj_payments.filter(status=PaymentStatus.PAID).aggregate(s=Sum("employee_payout")).get("s") or 0)

    stats = {
        "total_tasks":       task_total,
        "total_projects":    proj_total,
        "pending_requests":  task_pending,
        "total_hours":       tasks.aggregate(total=Sum("work_updates__hours_worked")).get("total") or 0,
        "pending":           task_pending,
        "active":            task_active,
        "completed":         task_completed,
        "submitted":         task_submitted,
        "rejected":          task_rejected,
        "total_revenue":     task_revenue + proj_revenue,
        "task_revenue":      task_revenue,
        "proj_revenue":      proj_revenue,
        "proj_active":       proj_active,
        "proj_completed":    proj_completed,
    }

    status_labels = ["Pending", "Active", "Submitted", "Completed", "Rejected"]
    status_data   = [task_pending, task_active, task_submitted, task_completed, task_rejected]

    # Project status breakdown
    proj_status_labels = ["Active", "Assigned", "Submitted", "Completed", "Closed"]
    proj_status_data   = [
        projects.filter(status="active").count(),
        projects.filter(status="assigned").count(),
        projects.filter(status="work_submitted").count(),
        projects.filter(status="completed").count(),
        projects.filter(status="closed").count(),
    ]

    payment_qs = Payment.objects.filter(task__employee=emp)
    chart_ctx  = _compute_chart_data(tasks, payment_qs, projects, proj_payments)

    q = (request.GET.get("q") or "").strip()
    tasks_show = nlp_filter_queryset(
        q,
        tasks,
        lambda t: f"{t.title} {t.client.profile.user.first_name} {t.client.profile.user.last_name} {t.client.company if hasattr(t.client,'company') else ''}"
    ) if q else list(tasks)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    recent_clients = (
        ClientProfile.objects.filter(tasks__employee=emp)
        .select_related("profile__user")
        .annotate(task_count=Count("tasks"))
        .distinct()
        .order_by("-id")[:5]
    )

    return render(request, "pages/dashboard/employee-dashboard.html", {
        "tasks":          tasks_show[:10],
        "projects":       projects[:8],
        "stats":          stats,
        "q":              q,
        "unread_count":   unread,
        "status_labels":       _json.dumps(status_labels),
        "status_data":         _json.dumps(status_data),
        "proj_status_labels":  _json.dumps(proj_status_labels),
        "proj_status_data":    _json.dumps(proj_status_data),
        "recent_clients":      recent_clients,
        **chart_ctx,
    })


@login_required
def dashboard_employee_task(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    tasks = TaskRequest.objects.filter(employee=emp).select_related("client__profile__user").order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    tasks = nlp_filter_queryset(
        q,
        tasks,
        lambda t: f"{t.title} {t.client.profile.user.first_name} {t.client.profile.user.last_name} {t.description}"
    ) if q else list(tasks)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/employee-task.html", {"tasks": tasks, "q": q, "unread_count": unread})


@login_required
def dashboard_task_detail(request: HttpRequest, task_id: Optional[int] = None) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    if task_id:
        task_obj = get_object_or_404(TaskRequest, id=task_id, employee=emp)
    else:
        task_obj = TaskRequest.objects.filter(employee=emp).order_by("-created_at").first()

    if request.method == "POST" and task_obj:
        new_status = request.POST.get("status")
        valid_statuses = [s[0] for s in TaskStatus.choices]
        if new_status in valid_statuses:
            task_obj.status = new_status
            task_obj.save()
            # Auto-create payment record when task is completed
            if new_status == TaskStatus.COMPLETED:
                if not hasattr(task_obj, 'payment') or not Payment.objects.filter(task=task_obj).exists():
                    _hours = task_obj.total_hours or 0
                    _rate  = task_obj.employee.hourly_rate or 0
                    amount = float(_hours) * float(_rate) if _hours and _rate else float(task_obj.estimated_cost or 0)
                    Payment.objects.get_or_create(
                        task=task_obj,
                        defaults={"client": task_obj.client, "amount": amount, "status": PaymentStatus.PENDING}
                    )
                Notification.objects.create(
                    user=task_obj.client.profile.user,
                    title="Task completed",
                    message=f"Your task '{task_obj.title}' has been marked as completed.",
                    link=f"/user_app/worksinner/{task_obj.id}/",
                )
            messages.success(request, f"Task status updated to {new_status}")
            return redirect("dashboard_task_detail_id", task_id=task_obj.id)

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(
        request,
        "pages/dashboard/task-detail.html",
        {
            "task": task_obj,
            "updates": task_obj.work_updates.order_by("-submitted_at") if task_obj else [],
            "task_statuses": TaskStatus.choices,
            "unread_notifications": unread,
        },
    )


@login_required
def dashboard_task_request(request: HttpRequest, task_id: Optional[int] = None) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    q = (request.GET.get("q") or "").strip()

    pending = TaskRequest.objects.filter(employee=emp, status=TaskStatus.PENDING).select_related("client__profile__user").order_by("-created_at")
    pending = nlp_filter_queryset(
        q,
        pending,
        lambda t: f"{t.title} {t.client.profile.user.first_name} {t.client.profile.user.last_name} {t.description}"
    ) if q else list(pending)

    if task_id is not None:
        task_obj = get_object_or_404(TaskRequest, id=task_id, employee=emp)
        action = request.GET.get("action")
        if action == "accept":
            task_obj.status = TaskStatus.ACCEPTED
            task_obj.save()
            Notification.objects.create(
                user=task_obj.client.profile.user,
                title="Task accepted",
                message=f"Your task '{task_obj.title}' was accepted.",
                link=f"/user_app/worksinner/{task_obj.id}/",
            )
            messages.success(request, "Task accepted")
            return redirect("dashboard_employee_task")
        if action == "reject":
            task_obj.status = TaskStatus.REJECTED
            task_obj.save()
            Notification.objects.create(
                user=task_obj.client.profile.user,
                title="Task rejected",
                message=f"Your task '{task_obj.title}' was rejected.",
                link="/user_app/works/",
            )
            messages.info(request, "Task rejected")
            return redirect("dashboard_task_request")

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/task-request.html", {"tasks": pending, "q": q, "unread_count": unread})


@login_required
def notifications(request: HttpRequest) -> HttpResponse:
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mark_all":
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect("notifications")
    q = (request.GET.get("q") or "").strip()
    notifications_list = nlp_filter_queryset(
        q, qs,
        lambda n: f"{n.title} {n.message}"
    ) if q else list(qs)
    return render(request, "pages/notifications.html", {
        "notifications": notifications_list,
        "q": q,
        "unread_count": qs.filter(is_read=False).count(),
    })


@login_required
def notification_read(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark a single notification as read and redirect to its link."""
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save()
    if n.link:
        return redirect(n.link)
    return redirect("notifications")


@login_required
def chat_with_employee(request: HttpRequest, employee_id: int) -> HttpResponse:
    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))

    client = ensure_client(profile)
    employee = get_object_or_404(EmployeeProfile.objects.select_related("profile__user"), id=employee_id)

    convo, _ = Conversation.objects.get_or_create(client=client, employee=employee)
    if request.method == "POST":
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = convo
            msg.sender = request.user
            msg.save()
            Notification.objects.create(
                user=employee.profile.user,
                title="New chat message",
                message=f"Message from {request.user.get_full_name() or request.user.username}",
                link=f"/employee_app/chat/{convo.id}/",
            )
            return redirect("chat_with_employee", employee_id=employee.id)
    else:
        form = ChatMessageForm()

    messages_qs = ChatMessage.objects.filter(conversation=convo).order_by("created_at")
    return render(request, "pages/chat.html", {
        "employee": employee,
        "messages": messages_qs,
        "form": form,
        "mode": "client",
    })


@login_required
def employee_chat_inbox(request: HttpRequest) -> HttpResponse:
    """Employee-side chat: open latest conversation or one specified by ?client=<id>."""
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    client_id = request.GET.get("client")

    convo_qs = Conversation.objects.filter(employee=emp).select_related(
        "client__profile__user", "employee__profile__user"
    ).order_by("-id")

    convo: Optional["Conversation"] = None
    if client_id and client_id.isdigit():
        convo = convo_qs.filter(client__id=int(client_id)).first()
    if convo is None:
        convo = convo_qs.first()

    # If no conversations yet, render chat page with empty state (no UI change; template already supports empty list)
    if convo is None:
        form = ChatMessageForm()
        return render(
            request,
            "pages/chat.html",
            {
                "employee": emp,
                "messages": [],
                "form": form,
                "inbox": convo_qs,
                "mode": "employee",
            },
        )

    return redirect("employee_chat", conversation_id=convo.id)


@login_required
def employee_chat(request: HttpRequest, conversation_id: int) -> HttpResponse:
    """Employee-side chat conversation view."""
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    convo = get_object_or_404(
        Conversation.objects.select_related("client__profile__user", "employee__profile__user"),
        id=conversation_id,
        employee=emp,
    )

    if request.method == "POST":
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = convo
            msg.sender = request.user
            msg.save()
            Notification.objects.create(
                user=convo.client.profile.user,
                title="New chat message",
                message=f"Message from {request.user.get_full_name() or request.user.username}",
                link=f"/chat/{convo.employee.id}/",
            )
            return redirect("employee_chat", conversation_id=convo.id)
    else:
        form = ChatMessageForm()

    messages_qs = ChatMessage.objects.filter(conversation=convo).order_by("created_at")
    inbox = Conversation.objects.filter(employee=emp).select_related("client__profile__user").order_by("-id")
    return render(
        request,
        "pages/chat.html",
        {
            "employee": emp,
            "client": convo.client,
            "conversation": convo,
            "messages": messages_qs,
            "form": form,
            "inbox": inbox,
            "mode": "employee",
        },
    )


@csrf_exempt
def chatbot(request: HttpRequest) -> HttpResponse:
    from django.http import JsonResponse
    import json, os

    if request.method != "POST":
        return JsonResponse({"reply": "Send POST JSON."})

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    msg = (data.get("message") or "").strip()
    history = data.get("history") or []  # list of {role, content} dicts

    if not msg:
        return JsonResponse({"reply": "Hi! I\'m the JobMate AI assistant. How can I help you today?"})

    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    # ── Try Anthropic Claude API ──────────────────────────────────────────────
    if api_key and not api_key.startswith("your-"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            system_prompt = """You are JobMate AI, a helpful assistant for the JobMate freelance platform.
JobMate connects clients with skilled employees/freelancers for short-term and hourly work.

Key features you can help with:
- Finding and browsing employees by skill, department, or name
- Requesting tasks from employees (clients can go to an employee profile and click REQUEST TASK)
- Tracking task status: Pending → Accepted → In Progress → Submitted → Completed
- Chat messaging between clients and employees
- Employee profiles with bio, skills, hourly rate, availability, testimonials, accreditations
- Revenue and payment tracking for employees
- Notifications for task updates and messages
- Dashboard for both clients and employees

Always be concise, helpful, and friendly. Answer in the same language the user writes in.
If asked something outside JobMate, politely redirect to JobMate topics."""

            messages = []
            for h in history[-10:]:  # send last 10 messages for context
                role = h.get("role", "user")
                text = h.get("content", "")
                if role in ("user", "assistant") and text:
                    messages.append({"role": role, "content": text})
            messages.append({"role": "user", "content": msg})

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=system_prompt,
                messages=messages,
            )
            reply = response.content[0].text.strip()
            return JsonResponse({"reply": reply})
        except Exception as e:
            # Fall through to keyword fallback
            pass

    # ── Keyword fallback (no API key or API error) ────────────────────────────
    msg_lower = msg.lower()
    if any(w in msg_lower for w in ["hello", "hi", "hey", "start", "help"]):
        reply = "Hi! I\'m the JobMate AI assistant. I can help you find employees, request tasks, track work, and more. What do you need?"
    elif any(w in msg_lower for w in ["search", "find", "look", "browse", "employee", "freelancer"]):
        reply = "You can search employees by name, skill, or department using the search bar on the Employees page. Each profile shows skills, hourly rate, and availability."
    elif any(w in msg_lower for w in ["task", "request", "hire", "work", "job"]):
        reply = "To request a task: go to an employee\'s profile and click REQUEST TASK. Fill in the title, description, budget and dates. The employee will accept or reject it."
    elif any(w in msg_lower for w in ["chat", "message", "talk", "contact"]):
        reply = "You can chat with employees directly. Open an employee\'s profile and click CHAT, or go to your Chat Inbox. You can send text messages and file attachments."
    elif any(w in msg_lower for w in ["payment", "pay", "money", "revenue", "invoice", "rate"]):
        reply = "Payments are tracked automatically based on the employee\'s hourly rate and hours logged. Check the Revenue page for a full breakdown of completed tasks and amounts."
    elif any(w in msg_lower for w in ["profile", "bio", "update", "edit", "photo"]):
        reply = "Go to My Profile to update your bio, skills, hourly rate, availability, profile photo, and banner image. Employees can also add testimonials and accreditations."
    elif any(w in msg_lower for w in ["notification", "alert", "update", "news"]):
        reply = "Notifications keep you updated on task acceptance, rejections, completions, and new messages. Click the 🔔 bell icon to view and manage them."
    elif any(w in msg_lower for w in ["status", "track", "progress"]):
        reply = "Task statuses: Pending (waiting for employee) → Accepted → In Progress → Submitted (work done) → Completed (client confirmed). Clients can mark tasks complete."
    elif any(w in msg_lower for w in ["attach", "file", "document", "upload", "image", "photo"]):
        reply = "You can attach files and images in chat messages — PDF, Word, Excel, images, ZIP and more. Click the 📎 paperclip button in the chat input area."
    else:
        reply = "I\'m here to help with JobMate! You can ask me about finding employees, requesting tasks, chat, payments, profiles, or notifications."

    return JsonResponse({"reply": reply})


@login_required
def dashboard_task_submit(request: HttpRequest, task_id: Optional[int] = None) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))

    if task_id is None:
        # If no task_id, redirect to task list
        return redirect("dashboard_employee_task")

    task_obj = get_object_or_404(TaskRequest, id=task_id, employee=emp)

    if request.method == "POST":
        form = WorkUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            upd: WorkUpdate = form.save(commit=False)
            upd.task = task_obj
            upd.employee = emp
            upd.save()
            task_obj.status = TaskStatus.SUBMITTED
            task_obj.save()
            # Notify client
            Notification.objects.create(
                user=task_obj.client.profile.user,
                title="Work submitted",
                message=f"Employee submitted work for '{task_obj.title}'",
                link=f"/user_app/worksinner/{task_obj.id}/",
            )
            messages.success(request, "Work submitted successfully")
            return redirect("dashboard_task_detail_id", task_id=task_obj.id)
        messages.error(request, "Please fix the errors below")
    else:
        form = WorkUpdateForm()

    updates = task_obj.work_updates.order_by("-submitted_at")
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/task-submit.html", {
        "task":         task_obj,
        "form":         form,
        "updates":      updates,
        "unread_notifications": unread,
        "hourly_rate":  emp.hourly_rate,
        "total_hours":  task_obj.total_hours,
        "estimated_cost": task_obj.estimated_cost,
    })


@login_required
def dashboard_employee_profile(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    profile = ensure_profile(request.user)
    emp = ensure_employee(profile)

    if request.method == "POST":
        pform = ProfileUpdateForm(request.POST, instance=profile, user=request.user)
        eform = EmployeeProfileUpdateForm(request.POST, request.FILES, instance=emp)
        if pform.is_valid() and eform.is_valid():
            pform.save()
            eform.save()
            messages.success(request, "Profile updated successfully")
            return redirect("dashboard_employee_profile")
        messages.error(request, "Please fix the errors below")
    else:
        pform = ProfileUpdateForm(instance=profile, user=request.user)
        eform = EmployeeProfileUpdateForm(instance=emp)

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    completed_count = emp.tasks.filter(status=TaskStatus.COMPLETED).count()
    testimonials = emp.testimonials.all()
    accreditations = emp.accreditations.all()
    portfolio_items = emp.portfolio_items.all()
    return render(request, "pages/dashboard/employee-profile.html", {
        "employee": emp,
        "pform": pform,
        "eform": eform,
        "unread_notifications": unread,
        "completed_tasks_count": completed_count,
        "testimonials": testimonials,
        "accreditations": accreditations,
        "portfolio_items": portfolio_items,
        "testimonial_form": TestimonialForm(),
        "accreditation_form": AccreditationForm(),
    })


@login_required
def employee_add_testimonial(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    if request.method == "POST":
        form = TestimonialForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.employee = emp
            t.save()
            messages.success(request, "Testimonial added.")
        else:
            messages.error(request, "Please fix the errors.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_edit_testimonial(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    t = get_object_or_404(Testimonial, pk=pk, employee=emp)
    if request.method == "POST":
        form = TestimonialForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial updated.")
        else:
            messages.error(request, "Please fix the errors.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_delete_testimonial(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    t = get_object_or_404(Testimonial, pk=pk, employee=emp)
    if request.method == "POST":
        t.delete()
        messages.success(request, "Testimonial deleted.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_add_accreditation(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    if request.method == "POST":
        form = AccreditationForm(request.POST, request.FILES)
        if form.is_valid():
            a = form.save(commit=False)
            a.employee = emp
            a.save()
            messages.success(request, "Accreditation added.")
        else:
            messages.error(request, "Please fix the errors.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_edit_accreditation(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    a = get_object_or_404(Accreditation, pk=pk, employee=emp)
    if request.method == "POST":
        form = AccreditationForm(request.POST, request.FILES, instance=a)
        if form.is_valid():
            form.save()
            messages.success(request, "Accreditation updated.")
        else:
            messages.error(request, "Please fix the errors.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_delete_accreditation(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    a = get_object_or_404(Accreditation, pk=pk, employee=emp)
    if request.method == "POST":
        a.delete()
        messages.success(request, "Accreditation deleted.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_add_portfolio(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    if request.method == "POST":
        title       = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        link        = request.POST.get("link", "").strip()
        date        = request.POST.get("date") or None
        image       = request.FILES.get("image")
        if title:
            item = Portfolio(employee=emp, title=title, description=description,
                             link=link, date=date)
            if image:
                item.image = image
            item.save()
            messages.success(request, "Portfolio item added.")
        else:
            messages.error(request, "Title is required.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_edit_portfolio(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    item = get_object_or_404(Portfolio, pk=pk, employee=emp)
    if request.method == "POST":
        title       = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        link        = request.POST.get("link", "").strip()
        date        = request.POST.get("date") or None
        image       = request.FILES.get("image")
        if title:
            item.title       = title
            item.description = description
            item.link        = link
            item.date        = date
            if image:
                item.image = image
            item.save()
            messages.success(request, "Portfolio item updated.")
        else:
            messages.error(request, "Title is required.")
    return redirect("dashboard_employee_profile")


@login_required
def employee_delete_portfolio(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_employee(request.user):
        return redirect("login")
    emp = ensure_employee(ensure_profile(request.user))
    item = get_object_or_404(Portfolio, pk=pk, employee=emp)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Portfolio item deleted.")
    return redirect("dashboard_employee_profile")


@login_required
def dashboard_clients(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    q = (request.GET.get("q") or "").strip()
    clients = (
        ClientProfile.objects.filter(tasks__employee=emp)
        .select_related("profile__user")
        .annotate(task_count=Count("tasks"))
        .distinct()
    )
    clients = nlp_filter_queryset(
        q,
        clients,
        lambda c: " ".join(filter(None, [
            c.profile.user.first_name,
            c.profile.user.last_name,
            c.profile.user.username,
            c.profile.user.email,
            c.company,
        ]))
    ) if q else list(clients)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/clients.html", {"clients": clients, "q": q, "unread_notifications": unread})


@login_required
def dashboard_revenue(request: HttpRequest) -> HttpResponse:
    if not is_employee(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    emp = ensure_employee(ensure_profile(request.user))
    q = (request.GET.get("q") or "").strip()

    # Task-based revenue
    completed_tasks = TaskRequest.objects.filter(
        employee=emp, status=TaskStatus.COMPLETED
    ).select_related("client__profile__user", "payment")
    completed_tasks = nlp_filter_queryset(
        q, completed_tasks,
        lambda t: " ".join(filter(None, [
            t.title, t.client.profile.user.first_name,
            t.client.profile.user.last_name, t.client.company, t.description,
        ]))
    ) if q else list(completed_tasks)

    task_total    = float(Payment.objects.filter(task__employee=emp).aggregate(t=Sum("amount")).get("t") or 0)
    task_paid     = float(Payment.objects.filter(task__employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    task_pending  = float(Payment.objects.filter(task__employee=emp, status=PaymentStatus.PENDING).aggregate(t=Sum("amount")).get("t") or 0)
    task_emp_payout = float(Payment.objects.filter(task__employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)
    task_admin_cut  = float(Payment.objects.filter(task__employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)

    # Project-based revenue — include accepted applications too
    completed_projects = Project.objects.filter(
        Q(assigned_to=emp) | Q(applications__employee=emp, applications__status="accepted"),
        status=ProjectStatus.COMPLETED
    ).distinct().select_related("client__profile__user", "payment")
    completed_projects = nlp_filter_queryset(
        q, completed_projects,
        lambda p: " ".join(filter(None, [
            p.title, p.client.profile.user.first_name,
            p.client.profile.user.last_name, p.description,
        ]))
    ) if q else list(completed_projects)

    project_total     = float(ProjectPayment.objects.filter(employee=emp).aggregate(t=Sum("amount")).get("t") or 0)
    proj_paid         = float(ProjectPayment.objects.filter(employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    proj_pending      = float(ProjectPayment.objects.filter(employee=emp, status=PaymentStatus.PENDING).aggregate(t=Sum("amount")).get("t") or 0)
    proj_emp_payout   = float(ProjectPayment.objects.filter(employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)
    proj_admin_cut    = float(ProjectPayment.objects.filter(employee=emp, status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)

    total_emp_payout  = task_emp_payout + proj_emp_payout
    total_admin_cut   = task_admin_cut + proj_admin_cut
    total             = float(task_total) + float(project_total)

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/revenue.html", {
        "total_revenue":    total,
        "task_total":       task_total,
        "task_paid":        task_paid,
        "task_pending":     task_pending,
        "task_emp_payout":  task_emp_payout,
        "task_admin_cut":   task_admin_cut,
        "project_total":    project_total,
        "proj_paid":        proj_paid,
        "proj_pending":     proj_pending,
        "proj_emp_payout":  proj_emp_payout,
        "proj_admin_cut":   proj_admin_cut,
        "total_emp_payout": total_emp_payout,
        "total_admin_cut":  total_admin_cut,
        "completed_tasks":  completed_tasks,
        "completed_projects": completed_projects,
        "q":                q,
        "unread_notifications": unread,
    })


# ---------------------------
# Admin dashboard
# ---------------------------


@login_required
def admin_add_employee(request):
    """Admin AJAX endpoint to create a new employee account directly."""
    import json as _json
    from .models import Department as _Dept, Skill as _Skill
    if not is_admin(request.user):
        from django.http import JsonResponse
        return JsonResponse({"ok": False, "error": "Unauthorized"}, status=403)
    if request.method == "POST":
        from django.http import JsonResponse
        data = request.POST
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        department_id = data.get("department", "")
        skill_id = data.get("skill", "")
        title = data.get("title", "").strip()
        hourly_rate = data.get("hourly_rate", "0").strip() or "0"
        # Validate
        errors = []
        if not full_name: errors.append("Full name is required.")
        if not email: errors.append("Email is required.")
        if not password: errors.append("Password is required.")
        if User.objects.filter(username=email).exists(): errors.append("An account with this email already exists.")
        if errors:
            return JsonResponse({"ok": False, "errors": errors})
        # Create user
        parts = full_name.split(" ", 1)
        first_name = parts[0]; last_name = parts[1] if len(parts) > 1 else ""
        user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name)
        profile = Profile.objects.create(user=user, role=UserRole.EMPLOYEE)
        emp = EmployeeProfile.objects.create(
            profile=profile,
            title=title,
            hourly_rate=hourly_rate,
            department_id=department_id if department_id else None,
            skill_id=skill_id if skill_id else None,
            approval_status=ApprovalStatus.APPROVED,
        )
        # Handle profile image
        if "profile_image" in request.FILES:
            emp.profile_image = request.FILES["profile_image"]
            emp.save()
        return JsonResponse({"ok": True, "message": f"Employee {full_name} added successfully!"})
    # GET - return departments/skills JSON for the modal
    from django.http import JsonResponse
    skills_by_dept = {}
    for sk in _Skill.objects.select_related("department").all():
        did = str(sk.department_id)
        if did not in skills_by_dept:
            skills_by_dept[did] = []
        skills_by_dept[did].append({"id": sk.id, "name": sk.name})
    depts = list(_Dept.objects.values("id", "name"))
    return JsonResponse({"departments": depts, "skills_by_dept": skills_by_dept})


@login_required
def dashboard_admin_dashboard(request: HttpRequest) -> HttpResponse:
    import json as _json
    from datetime import date as _date, timedelta as _td

    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    # Project stats
    all_projects_qs   = Project.objects.all()
    all_proj_pay_qs   = ProjectPayment.objects.all()
    proj_total        = all_projects_qs.count()
    proj_active       = all_projects_qs.filter(status__in=["active","assigned","work_submitted"]).count()
    proj_completed    = all_projects_qs.filter(status="completed").count()
    # Only PAID payments count as real revenue
    task_revenue_paid  = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    proj_revenue_paid  = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    total_revenue_paid = task_revenue_paid + proj_revenue_paid

    # Admin commission = 20% of paid revenue
    task_admin_comm    = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)
    proj_admin_comm    = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)
    total_admin_comm   = task_admin_comm + proj_admin_comm

    # Employee payouts = 80% of paid revenue
    task_emp_payout    = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)
    proj_emp_payout    = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)
    total_emp_payout   = task_emp_payout + proj_emp_payout

    stats = {
        "employees":       EmployeeProfile.objects.count(),
        "clients":         ClientProfile.objects.count(),
        "companies":       ClientProfile.objects.exclude(company="").values("company").distinct().count(),
        "tasks":           TaskRequest.objects.count(),
        "pending":         TaskRequest.objects.filter(status=TaskStatus.PENDING).count(),
        "active":          TaskRequest.objects.filter(status__in=[TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS]).count(),
        "completed":       TaskRequest.objects.filter(status=TaskStatus.COMPLETED).count(),
        # Revenue — PAID only
        "task_revenue":    task_revenue_paid,
        "proj_revenue":    proj_revenue_paid,
        "total_revenue":   total_revenue_paid,
        # Admin commission (20%)
        "admin_commission":    total_admin_comm,
        "task_admin_comm":     task_admin_comm,
        "proj_admin_comm":     proj_admin_comm,
        # Employee payouts (80%)
        "total_emp_payout":    total_emp_payout,
        # Project counts
        "proj_total":     proj_total,
        "proj_active":    proj_active,
        "proj_completed": proj_completed,
    }

    status_labels = ["Pending", "Active", "Submitted", "Completed", "Rejected"]
    status_data = [
        stats["pending"], stats["active"],
        TaskRequest.objects.filter(status=TaskStatus.SUBMITTED).count(),
        stats["completed"],
        TaskRequest.objects.filter(status=TaskStatus.REJECTED).count(),
    ]

    # Project status breakdown for admin
    proj_status_labels = ["Active", "Assigned", "Work Submitted", "Completed", "Closed"]
    proj_status_data   = [
        all_projects_qs.filter(status="active").count(),
        all_projects_qs.filter(status="assigned").count(),
        all_projects_qs.filter(status="work_submitted").count(),
        all_projects_qs.filter(status="completed").count(),
        all_projects_qs.filter(status="closed").count(),
    ]

    all_tasks_qs    = TaskRequest.objects.all()
    all_payments_qs = Payment.objects.all()
    chart_ctx = _compute_chart_data(all_tasks_qs, all_payments_qs, all_projects_qs, all_proj_pay_qs)

    q = (request.GET.get("q") or "").strip()
    recent_tasks_qs = TaskRequest.objects.select_related("client__profile__user", "employee__profile__user").order_by("-created_at")
    recent_projects_qs = Project.objects.select_related("client__profile__user", "assigned_to__profile__user").order_by("-created_at")
    employees_qs = EmployeeProfile.objects.select_related("profile__user").order_by("profile__user__first_name")

    if q:
        recent_tasks = nlp_filter_queryset(
            q, recent_tasks_qs,
            lambda t: f"{t.title} {t.client.profile.user.first_name} {t.client.profile.user.last_name}"
        )[:10]
        recent_projects = list(recent_projects_qs[:8])
        employees = nlp_filter_queryset(
            q, employees_qs,
            lambda e: f"{e.profile.user.first_name} {e.profile.user.last_name} {e.title}"
        )[:10]
    else:
        recent_tasks    = list(recent_tasks_qs[:10])
        recent_projects = list(recent_projects_qs[:8])
        employees       = list(employees_qs[:10])

    return render(
        request,
        "pages/dashboard/admin-dashboard.html",
        {
            "stats":            stats,
            "tasks":            recent_tasks,
            "projects":         recent_projects,
            "employees":        employees,
            "q":                q,
            "unread_notifications": Notification.objects.filter(user=request.user, is_read=False).count(),
            "status_labels":       _json.dumps(status_labels),
            "status_data":         _json.dumps(status_data),
            "proj_status_labels":  _json.dumps(proj_status_labels),
            "proj_status_data":    _json.dumps(proj_status_data),
            **chart_ctx,
        },
    )


@login_required
def dashboard_admin_employee(request: HttpRequest) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    q = (request.GET.get("q") or "").strip()
    tab = request.GET.get("tab", "pending")  # pending | approved | rejected

    qs = EmployeeProfile.objects.select_related("profile__user", "department", "skill").order_by("-profile__user__date_joined")
    if q:
        qs = nlp_filter_queryset(
            q,
            qs,
            lambda e: " ".join(filter(None, [
                e.profile.user.first_name,
                e.profile.user.last_name,
                e.profile.user.username,
                e.skill.name if e.skill else "",
                e.department.name if e.department else "",
                e.title,
                e.bio,
            ]))
        )
        counts = {
            "pending":  sum(1 for e in qs if e.approval_status == ApprovalStatus.PENDING),
            "approved": sum(1 for e in qs if e.approval_status == ApprovalStatus.APPROVED),
            "rejected": sum(1 for e in qs if e.approval_status == ApprovalStatus.REJECTED),
        }
        employees = [e for e in qs if e.approval_status == tab]
    else:
        counts = {
            "pending":  qs.filter(approval_status=ApprovalStatus.PENDING).count(),
            "approved": qs.filter(approval_status=ApprovalStatus.APPROVED).count(),
            "rejected": qs.filter(approval_status=ApprovalStatus.REJECTED).count(),
        }
        employees = list(qs.filter(approval_status=tab))
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/admin-employee.html", {
        "employees": employees, "q": q, "tab": tab, "counts": counts,
        "unread_notifications": unread,
        "tab_data": [("pending","⏳ Pending","#f57f17"),("approved","✅ Approved","#2e7d32"),("rejected","❌ Rejected","#c62828")],
    })


@login_required
def dashboard_admin_clients(request: HttpRequest) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    q = (request.GET.get("q") or "").strip()
    tab = request.GET.get("tab", "pending")  # pending | approved | rejected

    qs = ClientProfile.objects.select_related("profile__user").order_by("-profile__user__date_joined")
    if q:
        qs = nlp_filter_queryset(
            q,
            qs,
            lambda c: " ".join(filter(None, [
                c.profile.user.first_name,
                c.profile.user.last_name,
                c.profile.user.username,
                c.profile.user.email,
                c.company,
            ]))
        )
        counts = {
            "pending":  sum(1 for c in qs if c.approval_status == ApprovalStatus.PENDING),
            "approved": sum(1 for c in qs if c.approval_status == ApprovalStatus.APPROVED),
            "rejected": sum(1 for c in qs if c.approval_status == ApprovalStatus.REJECTED),
        }
        clients = [c for c in qs if c.approval_status == tab]
    else:
        counts = {
            "pending":  qs.filter(approval_status=ApprovalStatus.PENDING).count(),
            "approved": qs.filter(approval_status=ApprovalStatus.APPROVED).count(),
            "rejected": qs.filter(approval_status=ApprovalStatus.REJECTED).count(),
        }
        clients = list(qs.filter(approval_status=tab))
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/admin-clients.html", {
        "clients": clients, "q": q, "tab": tab, "counts": counts,
        "unread_notifications": unread,
        "tab_data": [("pending","⏳ Pending","#f57f17"),("approved","✅ Approved","#2e7d32"),("rejected","❌ Rejected","#c62828")],
    })


@login_required
def admin_approve_user(request: HttpRequest, user_type: str, pk: int) -> HttpResponse:
    """Approve an employee or client registration."""
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    if request.method != "POST":
        return redirect("dashboard_admin_employee" if user_type == "employee" else "dashboard_admin_clients")

    from django.utils import timezone as _tz
    if user_type == "employee":
        obj = get_object_or_404(EmployeeProfile, pk=pk)
        obj.approval_status = ApprovalStatus.APPROVED
        obj.approved_at = _tz.now()
        obj.rejected_reason = ""
        obj.save()
        Notification.objects.create(
            user=obj.profile.user,
            title="Registration Approved ✅",
            message="Your employee registration has been approved by the admin. You can now log in and use your dashboard.",
            link="/employee_app/employee-dashboard/",
        )
        messages.success(request, f"{obj.profile.user.get_full_name() or obj.profile.user.username} approved.")
        return redirect(f"{request.META.get('HTTP_REFERER', '/dashboard/admin-employee/')}#approved")
    else:
        obj = get_object_or_404(ClientProfile, pk=pk)
        obj.approval_status = ApprovalStatus.APPROVED
        obj.approved_at = _tz.now()
        obj.rejected_reason = ""
        obj.save()
        Notification.objects.create(
            user=obj.profile.user,
            title="Registration Approved ✅",
            message="Your client registration has been approved by the admin. You can now log in and use your dashboard.",
            link="/user_app/myprofile/",
        )
        messages.success(request, f"{obj.profile.user.get_full_name() or obj.profile.user.username} approved.")
        return redirect(f"{request.META.get('HTTP_REFERER', '/dashboard/admin-clients/')}#approved")


@login_required
def admin_reject_user(request: HttpRequest, user_type: str, pk: int) -> HttpResponse:
    """Reject an employee or client registration."""
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    if request.method != "POST":
        return redirect("dashboard_admin_employee" if user_type == "employee" else "dashboard_admin_clients")

    reason = request.POST.get("reason", "").strip()
    if user_type == "employee":
        obj = get_object_or_404(EmployeeProfile, pk=pk)
        obj.approval_status = ApprovalStatus.REJECTED
        obj.rejected_reason = reason
        obj.save()
        Notification.objects.create(
            user=obj.profile.user,
            title="Registration Rejected ❌",
            message=f"Your employee registration was not approved.{(' Reason: ' + reason) if reason else ''}",
            link="/register/",
        )
        messages.warning(request, f"{obj.profile.user.get_full_name() or obj.profile.user.username} rejected.")
        return redirect(f"{request.META.get('HTTP_REFERER', '/dashboard/admin-employee/')}#rejected")
    else:
        obj = get_object_or_404(ClientProfile, pk=pk)
        obj.approval_status = ApprovalStatus.REJECTED
        obj.rejected_reason = reason
        obj.save()
        Notification.objects.create(
            user=obj.profile.user,
            title="Registration Rejected ❌",
            message=f"Your client registration was not approved.{(' Reason: ' + reason) if reason else ''}",
            link="/register/",
        )
        messages.warning(request, f"{obj.profile.user.get_full_name() or obj.profile.user.username} rejected.")
        return redirect(f"{request.META.get('HTTP_REFERER', '/dashboard/admin-clients/')}#rejected")


@login_required
def admin_delete_user(request: HttpRequest, user_type: str, pk: int) -> HttpResponse:
    """Permanently delete an employee or client and their User account."""
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    if request.method != "POST":
        return redirect("dashboard_admin_employee" if user_type == "employee" else "dashboard_admin_clients")

    if user_type == "employee":
        obj = get_object_or_404(EmployeeProfile, pk=pk)
        name = obj.profile.user.get_full_name() or obj.profile.user.username
        obj.profile.user.delete()   # cascades to Profile → EmployeeProfile
        messages.success(request, f"Employee '{name}' deleted permanently.")
        return redirect("dashboard_admin_employee")
    else:
        obj = get_object_or_404(ClientProfile, pk=pk)
        name = obj.profile.user.get_full_name() or obj.profile.user.username
        obj.profile.user.delete()   # cascades to Profile → ClientProfile
        messages.success(request, f"Client '{name}' deleted permanently.")
        return redirect("dashboard_admin_clients")


@login_required
def dashboard_admin_departments(request: HttpRequest) -> HttpResponse:
    """Admin: list all departments with add/edit/delete."""
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    q = (request.GET.get("q") or "").strip()
    departments = Department.objects.annotate(
        skill_count=Count("skills"),
        emp_count=Count(
            "skills__employeeprofile",
            filter=Q(skills__employeeprofile__approval_status="approved"),
        ),
    ).order_by("name")
    departments = nlp_filter_queryset(
        q,
        departments,
        lambda d: f"{d.name} {d.description}"
    ) if q else list(departments)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/admin-departments.html", {
        "departments": departments,
        "q": q,
        "unread_notifications": unread,
    })


@login_required
def dashboard_admin_department_add(request: HttpRequest) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            if Department.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Department '{name}' already exists.")
            else:
                dept = Department.objects.create(name=name, description=description)
                if "image" in request.FILES:
                    dept.image = request.FILES["image"]
                    dept.save()
                messages.success(request, f"Department '{name}' added successfully.")
        else:
            messages.error(request, "Department name is required.")
    return redirect("dashboard_admin_departments")


@login_required
def dashboard_admin_department_edit(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            dept.name = name
            dept.description = description
            if "image" in request.FILES:
                dept.image = request.FILES["image"]
            elif request.POST.get("clear_image") == "1":
                dept.image = None
            dept.save()
            messages.success(request, f"Department '{name}' updated.")
        else:
            messages.error(request, "Department name is required.")
    return redirect("dashboard_admin_departments")


@login_required
def dashboard_admin_department_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' deleted.")
    return redirect("dashboard_admin_departments")


@login_required
def dashboard_admin_revenue(request: HttpRequest) -> HttpResponse:
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    # ── Per-table search params ──────────────────────────────────────────────
    q       = (request.GET.get("q")       or "").strip()   # legacy global
    q_task  = (request.GET.get("q_task")  or q).strip()    # Task Payments table
    q_proj  = (request.GET.get("q_proj")  or q).strip()    # Project Payments table
    q_emp   = (request.GET.get("q_emp")   or "").strip()   # Employee Breakdown table

    # Task payments
    payments = Payment.objects.select_related(
        "task__employee__profile__user", "client__profile__user"
    ).order_by("-id")
    payments = nlp_filter_queryset(
        q_task, payments,
        lambda p: " ".join(filter(None, [
            p.task.title if p.task else "",
            p.task.employee.profile.user.get_full_name() if p.task and p.task.employee else "",
            p.client.profile.user.get_full_name() or p.client.profile.user.username,
            p.client.company if hasattr(p.client, 'company') else "",
            p.status, p.method,
        ]))
    ) if q_task else list(payments)

    # Project payments
    project_payments = ProjectPayment.objects.select_related(
        "project", "employee__profile__user", "client__profile__user"
    ).order_by("-created_at")
    project_payments = nlp_filter_queryset(
        q_proj, project_payments,
        lambda pp: " ".join(filter(None, [
            pp.project.title,
            pp.employee.profile.user.get_full_name() or pp.employee.profile.user.username,
            pp.client.profile.user.get_full_name() or pp.client.profile.user.username,
            pp.status,
        ]))
    ) if q_proj else list(project_payments)

    task_total          = float(Payment.objects.aggregate(t=Sum("amount")).get("t") or 0)
    task_paid           = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    task_pending_amt    = float(Payment.objects.filter(status=PaymentStatus.PENDING).aggregate(t=Sum("amount")).get("t") or 0)
    task_admin_comm     = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)
    task_emp_payout     = float(Payment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)

    project_total       = float(ProjectPayment.objects.aggregate(t=Sum("amount")).get("t") or 0)
    proj_paid           = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("amount")).get("t") or 0)
    proj_pending_amt    = float(ProjectPayment.objects.filter(status=PaymentStatus.PENDING).aggregate(t=Sum("amount")).get("t") or 0)
    proj_admin_comm     = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("admin_commission")).get("t") or 0)
    proj_emp_payout     = float(ProjectPayment.objects.filter(status=PaymentStatus.PAID).aggregate(t=Sum("employee_payout")).get("t") or 0)

    grand_total         = task_total + project_total
    total_admin_revenue = task_admin_comm + proj_admin_comm
    total_emp_payout    = task_emp_payout + proj_emp_payout

    # Per-employee project revenue breakdown
    from django.db.models import Count
    _raw_emp = (
        ProjectPayment.objects
        .select_related("employee__profile__user")
        .values(
            "employee__id",
            "employee__profile__user__first_name",
            "employee__profile__user__last_name",
            "employee__profile__user__username",
            "employee__title",
        )
        .annotate(total=Sum("amount"), proj_count=Count("id"))
        .order_by("-total")
    )
    emp_proj_revenue_all = [
        {
            "emp_id":     r["employee__id"],
            "full_name":  (
                f"{r['employee__profile__user__first_name']} {r['employee__profile__user__last_name']}".strip()
                or r["employee__profile__user__username"] or "Unknown"
            ),
            "title":      r["employee__title"] or "",
            "total":      r["total"] or 0,
            "count":      r["proj_count"],
            "initial":    (r["employee__profile__user__first_name"] or r["employee__profile__user__username"] or "?")[0].upper(),
        }
        for r in _raw_emp
    ]
    # NLP filter the employee breakdown rows
    if q_emp:
        q_lower = q_emp.lower()
        emp_proj_revenue = [
            row for row in emp_proj_revenue_all
            if q_lower in row["full_name"].lower()
            or q_lower in row["title"].lower()
        ]
    else:
        emp_proj_revenue = emp_proj_revenue_all

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/admin-revenue.html", {
        "payments":             payments,
        "project_payments":     project_payments,
        "task_total":           task_total,
        "task_paid":            task_paid,
        "task_pending_amt":     task_pending_amt,
        "task_admin_comm":      task_admin_comm,
        "task_emp_payout":      task_emp_payout,
        "project_total":        project_total,
        "proj_paid":            proj_paid,
        "proj_pending_amt":     proj_pending_amt,
        "proj_admin_comm":      proj_admin_comm,
        "proj_emp_payout":      proj_emp_payout,
        "grand_total":          grand_total,
        "total_admin_revenue":  total_admin_revenue,
        "total_emp_payout":     total_emp_payout,
        "emp_proj_revenue":     emp_proj_revenue,
        "q": q, "q_task": q_task, "q_proj": q_proj, "q_emp": q_emp,
        "unread_notifications": unread,
    })



@login_required
def download_work_file(request: HttpRequest, update_id: int) -> HttpResponse:
    """Secure download: only the client who owns the task can download the work file."""
    from django.http import FileResponse, Http404
    import os

    upd = get_object_or_404(WorkUpdate, id=update_id)

    # Check access: must be the task's client OR admin
    is_owner_client = (
        request.user.profile.role == UserRole.CLIENT
        and hasattr(request.user.profile, 'client')
        and upd.task.client == request.user.profile.client
    )
    if not (is_owner_client or request.user.is_superuser):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to download this file.")

    if not upd.work_file:
        from django.contrib import messages
        messages.error(request, "No file has been uploaded for this work update.")
        return redirect('worksinner_id', task_id=upd.task_id)

    try:
        response = FileResponse(upd.work_file.open('rb'), as_attachment=True)
        filename = upd.work_file.name.split('/')[-1]
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except FileNotFoundError:
        from django.http import Http404
        raise Http404("File not found.")


@login_required
def admin_employee_revenue_detail(request: HttpRequest, employee_id: int) -> HttpResponse:
    """Admin view: revenue chart for a specific employee."""
    import json as _json
    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    # Allow the in-page selector to override via GET param
    override_id = request.GET.get('emp_id')
    if override_id and override_id.isdigit():
        employee_id = int(override_id)
        return redirect('admin_employee_revenue_detail', employee_id=employee_id)
    emp = get_object_or_404(EmployeeProfile.objects.select_related('profile__user'), id=employee_id)
    emp_tasks = TaskRequest.objects.filter(employee=emp)
    emp_payments = Payment.objects.filter(task__employee=emp)

    task_revenue = emp_payments.filter(task__status=TaskStatus.COMPLETED).aggregate(t=Sum('amount')).get('t') or 0
    proj_revenue = ProjectPayment.objects.filter(employee=emp).aggregate(t=Sum('amount')).get('t') or 0
    total_revenue = float(task_revenue) + float(proj_revenue)

    completed = emp_tasks.filter(status=TaskStatus.COMPLETED).count()
    active = emp_tasks.filter(status__in=[TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS]).count()
    pending = emp_tasks.filter(status=TaskStatus.PENDING).count()

    emp_all_projects = Project.objects.filter(
        Q(assigned_to=emp) | Q(applications__employee=emp, applications__status="accepted")
    ).distinct()

    completed_projects = emp_all_projects.filter(
        status=ProjectStatus.COMPLETED
    ).select_related("client__profile__user", "payment")

    # Project status breakdown for chart
    proj_status_labels = ["Active", "Assigned", "Work Submitted", "Completed", "Closed"]
    proj_status_data   = [
        emp_all_projects.filter(status="active").count(),
        emp_all_projects.filter(status="assigned").count(),
        emp_all_projects.filter(status="work_submitted").count(),
        emp_all_projects.filter(status="completed").count(),
        emp_all_projects.filter(status="closed").count(),
    ]

    emp_proj_payments = ProjectPayment.objects.filter(employee=emp)
    chart_ctx = _compute_chart_data(emp_tasks, emp_payments, emp_all_projects, emp_proj_payments)

    status_labels = ["Pending", "Active", "Submitted", "Completed", "Rejected"]
    status_data = [
        pending, active,
        emp_tasks.filter(status=TaskStatus.SUBMITTED).count(),
        completed,
        emp_tasks.filter(status=TaskStatus.REJECTED).count(),
    ]

    all_employees = EmployeeProfile.objects.select_related('profile__user').order_by('profile__user__first_name')
    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'pages/dashboard/admin-employee-revenue.html', {
        'emp': emp,
        'total_revenue': total_revenue,
        'task_revenue': task_revenue,
        'proj_revenue': proj_revenue,
        'completed': completed,
        'active': active,
        'pending': pending,
        'completed_projects': completed_projects,
        'all_employees': all_employees,
        'unread_notifications': unread,
        'status_labels':      _json.dumps(status_labels),
        'status_data':        _json.dumps(status_data),
        'proj_status_labels': _json.dumps(proj_status_labels),
        'proj_status_data':   _json.dumps(proj_status_data),
        **chart_ctx,
    })



@login_required
def dashboard_employeelogin(request: HttpRequest) -> HttpResponse:
    return redirect("employee_login")

# ─────────────────────────────────────────────────────────────────────────────
# NLP Search API  —  JSON endpoint used by all page search boxes
# GET /api/nlp-search/?page=<page_key>&q=<query>
# ─────────────────────────────────────────────────────────────────────────────
def nlp_search_api(request: HttpRequest) -> "JsonResponse":
    """
    Returns NLP-ranked JSON results for the given page and query.
    Used by the live search boxes on each page (JS fetch).
    Public page keys (employees, departments) work for anonymous users.
    """
    from django.http import JsonResponse

    page_key = request.GET.get("page", "")
    q = (request.GET.get("q") or "").strip()

    if not q:
        return JsonResponse({"results": [], "query": q})

    results = []

    if page_key == "employees":
        qs = EmployeeProfile.objects.select_related(
            "profile__user", "department", "skill"
        ).filter(approval_status="approved")
        items = nlp_filter_queryset(q, qs, lambda e: " ".join(filter(None, [
            e.profile.user.get_full_name() or e.profile.user.username,
            e.title, e.bio,
            e.skill.name if e.skill else "",
            e.department.name if e.department else "",
        ])))
        results = [{
            "id": e.pk,
            "label": e.profile.user.get_full_name() or e.profile.user.username,
            "sub": (e.skill.name if e.skill else "") + (" · " + e.department.name if e.department else ""),
            "url": f"/empprofile/{e.pk}/",
        } for e in items[:12]]

    elif page_key == "departments":
        from django.db.models import Count as _C
        qs = Department.objects.annotate(
            emp_count=_C("skills__employeeprofile",
                         filter=Q(skills__employeeprofile__approval_status="approved"))
        )
        items = nlp_filter_queryset(q, qs, lambda d: f"{d.name} {d.description}")
        results = [{
            "id": d.pk,
            "label": d.name,
            "sub": f"{d.emp_count} professionals",
            "url": f"/rolesinner/{d.pk}/",
        } for d in items[:12]]

    elif page_key == "works":
        profile = ensure_profile(request.user)
        client = ensure_client(profile)
        qs = TaskRequest.objects.filter(client=client).select_related("employee__profile__user").order_by("-created_at")
        items = nlp_filter_queryset(q, qs, lambda t: f"{t.title} {t.description} {t.status}")
        results = [{
            "id": t.pk,
            "label": t.title,
            "sub": t.get_status_display() if hasattr(t, "get_status_display") else t.status,
            "url": f"/user_app/worksinner/{t.pk}/",
        } for t in items[:12]]

    elif page_key == "payments":
        profile = ensure_profile(request.user)
        client = ensure_client(profile)
        qs = Payment.objects.filter(client=client).select_related("task").order_by("-id")
        items = nlp_filter_queryset(q, qs, lambda p: f"{p.task.title if p.task else ''} {p.status} {p.method} {p.amount}")
        results = [{
            "id": p.pk,
            "label": p.task.title if p.task else f"Payment #{p.pk}",
            "sub": f"{p.status} · ₹{p.amount}",
            "url": "/user_app/payments/",
        } for p in items[:12]]

    elif page_key == "support":
        qs = request.user.supportticket_set.all().order_by("-created_at")
        items = nlp_filter_queryset(q, qs, lambda t: f"{t.subject} {t.message}")
        results = [{
            "id": t.pk,
            "label": t.subject,
            "sub": t.status,
            "url": "/user_app/support/",
        } for t in items[:12]]
        # Also search FAQs
        faq_qs = FAQ.objects.filter(is_active=True)
        faq_items = nlp_filter_queryset(q, faq_qs, lambda f: f"{f.question} {f.answer}")
        results += [{
            "id": f"faq_{f.pk}",
            "label": f.question,
            "sub": "FAQ",
            "url": "/user_app/support/",
        } for f in faq_items[:6]]

    elif page_key == "notifications":
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        items = nlp_filter_queryset(q, qs, lambda n: f"{n.title} {n.message}")
        results = [{
            "id": n.pk,
            "label": n.title,
            "sub": n.message[:60] + "…" if len(n.message) > 60 else n.message,
            "url": f"/notifications/{n.pk}/read/",
        } for n in items[:12]]

    elif page_key == "tasks_emp":
        emp = ensure_employee(ensure_profile(request.user))
        qs = TaskRequest.objects.filter(employee=emp).select_related("client__profile__user").order_by("-created_at")
        items = nlp_filter_queryset(q, qs, lambda t: f"{t.title} {t.description} {t.status}")
        results = [{
            "id": t.pk,
            "label": t.title,
            "sub": f"{t.client.profile.user.get_full_name()} · {t.status}",
            "url": f"/employee_app/task-detail/{t.pk}/",
        } for t in items[:12]]

    elif page_key == "admin_employees":
        qs = EmployeeProfile.objects.select_related("profile__user", "department", "skill")
        items = nlp_filter_queryset(q, qs, lambda e: " ".join(filter(None, [
            e.profile.user.get_full_name(), e.profile.user.username,
            e.title, e.bio,
            e.skill.name if e.skill else "",
            e.department.name if e.department else "",
        ])))
        results = [{
            "id": e.pk,
            "label": e.profile.user.get_full_name() or e.profile.user.username,
            "sub": (e.skill.name if e.skill else "") + (" · " + e.department.name if e.department else ""),
            "url": f"/admin_app/admin-employee/?q={q}",
        } for e in items[:12]]

    elif page_key == "admin_clients":
        qs = ClientProfile.objects.select_related("profile__user")
        items = nlp_filter_queryset(q, qs, lambda c: " ".join(filter(None, [
            c.profile.user.get_full_name(), c.profile.user.username,
            c.profile.user.email, c.company,
        ])))
        results = [{
            "id": c.pk,
            "label": c.profile.user.get_full_name() or c.profile.user.username,
            "sub": c.company or c.profile.user.email,
            "url": f"/admin_app/admin-clients/?q={q}",
        } for c in items[:12]]

    elif page_key == "admin_revenue":
        qs = Payment.objects.select_related("task", "client__profile__user").order_by("-id")
        items = nlp_filter_queryset(q, qs, lambda p: " ".join(filter(None, [
            p.task.title if p.task else "",
            p.client.profile.user.get_full_name(),
            p.client.company, p.status, p.method,
        ])))
        results = [{
            "id": p.pk,
            "label": p.task.title if p.task else f"Payment #{p.pk}",
            "sub": f"{p.client.profile.user.get_full_name()} · {p.status}",
            "url": f"/admin_app/admin-revenue/?q={q}",
        } for p in items[:12]]

    return JsonResponse({"results": results, "query": q})


# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT FEATURE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def client_projects(request):
    """Client: list own projects + create new."""
    profile = ensure_profile(request.user)
    if profile.role != UserRole.CLIENT and not request.user.is_superuser:
        return redirect(_role_redirect(profile))
    client = ensure_client(profile)

    if request.method == "POST":
        action = request.POST.get("action")

        # ── Create project ──────────────────────────────────────────────────
        if action == "create":
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "").strip()
            budget = request.POST.get("budget") or 0
            dept_id = request.POST.get("department") or None
            skill_id = request.POST.get("skill") or None

            # ── Smart deadline: date-only OR datetime (within-24h mode) ──────
            deadline = None
            deadline_mode = request.POST.get("deadline_mode", "date")   # "date" | "hours"
            raw_deadline  = request.POST.get("deadline", "").strip()
            raw_hours     = request.POST.get("deadline_hours", "").strip()

            if deadline_mode == "hours" and raw_hours:
                # Client wants delivery within N hours from now
                from django.utils import timezone as _tz
                from datetime import timedelta as _td
                try:
                    hrs = float(raw_hours)
                    if hrs <= 0:
                        raise ValueError
                    deadline = _tz.now() + _td(hours=hrs)
                except (ValueError, TypeError):
                    messages.error(request, "Please enter a valid number of hours.")
                    return redirect("client_projects")
            elif raw_deadline:
                # Standard date or datetime string from input[type=datetime-local]
                from django.utils import timezone as _tz
                from datetime import datetime as _dt
                try:
                    # Try datetime-local format first (YYYY-MM-DDTHH:MM)
                    if "T" in raw_deadline:
                        naive = _dt.strptime(raw_deadline, "%Y-%m-%dT%H:%M")
                    else:
                        # Date-only → set to end of that day 23:59
                        naive = _dt.strptime(raw_deadline, "%Y-%m-%d").replace(hour=23, minute=59)
                    # Make timezone-aware
                    deadline = _tz.make_aware(naive, _tz.get_current_timezone())
                except (ValueError, TypeError):
                    messages.error(request, "Invalid deadline format.")
                    return redirect("client_projects")

            if title and description:
                Project.objects.create(
                    client=client, title=title, description=description,
                    budget=budget, deadline=deadline,
                    department_id=dept_id or None,
                    skill_id=skill_id or None,
                    status=ProjectStatus.ACTIVE,
                )
                messages.success(request, f"Project '{title}' created successfully!")
            else:
                messages.error(request, "Title and description are required.")
            return redirect("client_projects")

        # ── Accept an application ───────────────────────────────────────────
        if action == "accept_application":
            app_id = request.POST.get("application_id")
            app = get_object_or_404(ProjectApplication, id=app_id, project__client=client)
            if app.project.status == ProjectStatus.ACTIVE:
                app.status = ProjectApplicationStatus.ACCEPTED
                app.save()
                ProjectApplication.objects.filter(
                    project=app.project
                ).exclude(id=app.id).update(status=ProjectApplicationStatus.REJECTED)
                app.project.status = ProjectStatus.ASSIGNED
                app.project.assigned_to = app.employee
                app.project.save()
                Notification.objects.create(
                    user=app.employee.profile.user,
                    title="Project Application Accepted! 🎉",
                    message=f"Your application for \'{app.project.title}\' has been accepted. Please upload your work when ready.",
                    link="/employee_app/employee-projects/",
                )
                messages.success(request, f"Accepted {app.employee.profile.user.get_full_name() or app.employee.profile.user.username} for \'{app.project.title}\'.")
            else:
                messages.error(request, "This project has already been assigned.")
            return redirect("client_projects")

        # ── Reject an application ───────────────────────────────────────────
        if action == "reject_application":
            app_id = request.POST.get("application_id")
            app = get_object_or_404(ProjectApplication, id=app_id, project__client=client)
            app.status = ProjectApplicationStatus.REJECTED
            app.save()
            Notification.objects.create(
                user=app.employee.profile.user,
                title="Project Application Update",
                message=f"Your application for \'{app.project.title}\' was not selected this time.",
                link="/employee_app/employee-projects/",
            )
            messages.success(request, "Application rejected.")
            return redirect("client_projects")

        # ── Mark project as COMPLETE (after work submitted) ────────────────
        if action == "mark_complete":
            proj_id = request.POST.get("project_id")
            proj = get_object_or_404(Project, id=proj_id, client=client)
            if proj.status == ProjectStatus.WORK_SUBMITTED:
                proj.status = ProjectStatus.COMPLETED
                proj.completed_at = timezone.now()
                proj.save()
                # Create ProjectPayment record
                if not ProjectPayment.objects.filter(project=proj).exists():
                    ProjectPayment.objects.create(
                        project=proj,
                        employee=proj.assigned_to,
                        client=client,
                        amount=proj.budget or 0,
                        status=PaymentStatus.PENDING,
                    )
                Notification.objects.create(
                    user=proj.assigned_to.profile.user,
                    title="Project Marked as Completed! 🎉",
                    message=f"Client has marked \'{proj.title}\' as completed. Payment of ₹{proj.budget} is being processed.",
                    link="/employee_app/employee-projects/",
                )
                messages.success(request, f"\'{proj.title}\' marked as completed! Payment record created.")
            else:
                messages.error(request, "Project can only be completed after the employee submits their work.")
            return redirect("client_projects")

        # ── Close project ───────────────────────────────────────────────────
        if action == "close_project":
            proj_id = request.POST.get("project_id")
            proj = get_object_or_404(Project, id=proj_id, client=client)
            proj.status = ProjectStatus.CLOSED
            proj.save()
            messages.success(request, f"Project \'{proj.title}\' closed.")
            return redirect("client_projects")

    projects = Project.objects.filter(client=client).prefetch_related(
        "applications__employee__profile__user",
        "applications__employee__portfolio_items",
        "applications__employee__testimonials",
        "applications__employee__accreditations",
        "applications__employee__department",
        "applications__employee__skill",
    ).select_related(
        "department", "skill",
        "assigned_to__profile__user",
    )
    departments = Department.objects.all()
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/client-projects.html", {
        "projects": projects,
        "departments": departments,
        "unread_count": unread,
    })

@login_required
def employee_projects(request):
    """Employee: browse active projects + apply + submit work."""
    profile = ensure_profile(request.user)
    if profile.role != UserRole.EMPLOYEE and not request.user.is_superuser:
        return redirect(_role_redirect(profile))
    employee = ensure_employee(profile)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "apply":
            proj_id = request.POST.get("project_id")
            message = request.POST.get("message", "").strip()
            proj = get_object_or_404(Project, id=proj_id, status=ProjectStatus.ACTIVE)
            if ProjectApplication.objects.filter(project=proj, employee=employee).exists():
                messages.error(request, "You have already applied to this project.")
            else:
                ProjectApplication.objects.create(
                    project=proj, employee=employee, message=message,
                    status=ProjectApplicationStatus.PENDING,
                )
                Notification.objects.create(
                    user=proj.client.profile.user,
                    title="New Project Application",
                    message=f"{request.user.get_full_name() or request.user.username} applied for \'{proj.title}\'.",
                    link="/user_app/projects/",
                )
                messages.success(request, f"Applied to \'{proj.title}\' successfully!")
            return redirect("employee_projects")

        if action == "withdraw":
            proj_id = request.POST.get("project_id")
            app = get_object_or_404(ProjectApplication, project_id=proj_id, employee=employee, status=ProjectApplicationStatus.PENDING)
            app.delete()
            messages.success(request, "Application withdrawn.")
            return redirect("employee_projects")

        # ── Submit work file ────────────────────────────────────────────────
        if action == "submit_work":
            proj_id = request.POST.get("project_id")
            proj = get_object_or_404(Project, id=proj_id, assigned_to=employee, status=ProjectStatus.ASSIGNED)
            work_file = request.FILES.get("work_file")
            work_note = request.POST.get("work_note", "").strip()
            if work_file:
                proj.work_file = work_file
                proj.work_note = work_note
                proj.status = ProjectStatus.WORK_SUBMITTED
                proj.work_submitted_at = timezone.now()
                proj.save()
                Notification.objects.create(
                    user=proj.client.profile.user,
                    title="Project Work Submitted! 📎",
                    message=f"{request.user.get_full_name() or request.user.username} has submitted work for \'{proj.title}\'. Please review and mark as complete.",
                    link="/user_app/projects/",
                )
                messages.success(request, f"Work submitted for \'{proj.title}\'. Waiting for client to mark as complete.")
            else:
                messages.error(request, "Please select a file to upload.")
            return redirect("employee_projects")

    active_projects = Project.objects.filter(
        status=ProjectStatus.ACTIVE
    ).select_related("client__profile__user", "client", "department", "skill")

    my_applications = list(
        ProjectApplication.objects.filter(employee=employee)
        .select_related("project__client__profile__user", "project__department", "project__skill")
        .order_by("-applied_at")
    )
    my_applied_ids = {a.project_id for a in my_applications}

    my_assigned = Project.objects.filter(
        assigned_to=employee, status__in=[ProjectStatus.ASSIGNED, ProjectStatus.WORK_SUBMITTED, ProjectStatus.COMPLETED]
    ).select_related("client__profile__user")

    departments = Department.objects.all()
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/employee-projects.html", {
        "active_projects": active_projects,
        "my_applications": my_applications,
        "my_applied_ids": my_applied_ids,
        "my_assigned": my_assigned,
        "departments": departments,
        "unread_count": unread,
    })

@login_required
def client_projects_skills_json(request):
    """AJAX: return skills for a department."""
    dept_id = request.GET.get("dept_id")
    if dept_id:
        skills = list(Skill.objects.filter(department_id=dept_id).values("id", "name"))
    else:
        skills = []
    from django.http import JsonResponse
    return JsonResponse({"skills": skills})


@login_required
def download_project_file(request, project_id):
    """Secure download of project work file — client or assigned employee only."""
    from django.http import FileResponse, Http404
    proj = get_object_or_404(Project, id=project_id)
    profile = ensure_profile(request.user)
    is_owner = (
        (profile.role == UserRole.CLIENT and hasattr(profile, 'client') and proj.client == profile.client)
        or (profile.role == UserRole.EMPLOYEE and hasattr(profile, 'employee') and proj.assigned_to == profile.employee)
        or request.user.is_superuser
    )
    if not is_owner:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access denied.")
    if not proj.work_file:
        messages.error(request, "No file has been uploaded for this project.")
        return redirect("client_projects")
    try:
        response = FileResponse(proj.work_file.open('rb'), as_attachment=True)
        filename = proj.work_file.name.split('/')[-1]
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except FileNotFoundError:
        from django.http import Http404
        raise Http404("File not found.")


@login_required
def project_applicant_profile_json(request, app_id):
    """AJAX: return full employee profile data for a project application."""
    from django.http import JsonResponse
    import json as _json

    profile = ensure_profile(request.user)
    # Only clients (or admin) can view this
    if profile.role not in (UserRole.CLIENT, UserRole.ADMIN) and not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    app = get_object_or_404(
        ProjectApplication.objects.select_related(
            "project__client__profile__user",
            "employee__profile__user",
            "employee__department",
            "employee__skill",
        ).prefetch_related(
            "employee__portfolio_items",
            "employee__testimonials",
            "employee__accreditations",
        ),
        id=app_id
    )

    # If client, verify they own this project
    if profile.role == UserRole.CLIENT:
        client = ensure_client(profile)
        if app.project.client != client:
            return JsonResponse({"error": "Unauthorized"}, status=403)

    emp = app.employee
    user = emp.profile.user

    data = {
        "appId": app.id,
        "projId": app.project.id,
        "projTitle": app.project.title,
        "name": user.get_full_name() or user.username,
        "title": emp.title or "",
        "bio": emp.bio or "",
        "department": emp.department.name if emp.department else "",
        "skill": emp.skill.name if emp.skill else "",
        "hourlyRate": f"₹{emp.hourly_rate}/hr" if emp.hourly_rate else "",
        "avatar": emp.profile_image.url if emp.profile_image else "",
        "empProfileUrl": f"/empprofile/{emp.id}/",
        "message": app.message or "",
        "portfolio": [
            {"title": p.title, "desc": p.description[:120] if p.description else "", "link": p.link or ""}
            for p in emp.portfolio_items.all()
        ],
        "testimonials": [
            {"author": t.author_name, "text": t.text[:150] if t.text else "", "rating": t.rating}
            for t in emp.testimonials.all()
        ],
        "accreditations": [
            {"title": a.title, "org": a.issuer or ""}
            for a in emp.accreditations.all()
        ],
    }
    return JsonResponse(data)


@login_required
def notification_count_json(request):
    """AJAX: return current unread notification count."""
    from django.http import JsonResponse
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})


@login_required
def notification_mark_all_read_json(request):
    """AJAX POST: mark all notifications as read, return new count."""
    from django.http import JsonResponse
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})


# ══════════════════════════════════════════════════════════════════════════════
#  BANK DETAILS — Employee & Client add/edit their bank account
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def bank_detail_view(request):
    """Employee or Client: add/edit their bank account details.
    On save, automatically creates a Razorpay Contact + Fund Account."""
    from django.conf import settings as djsettings
    from django.http import JsonResponse

    profile = ensure_profile(request.user)
    if profile.role not in (UserRole.EMPLOYEE, UserRole.CLIENT):
        return redirect(_role_redirect(profile))

    # Get or init existing bank detail
    try:
        instance = request.user.bank_detail
    except BankDetail.DoesNotExist:
        instance = None

    if request.method == "POST":
        form = BankDetailForm(request.POST, instance=instance)
        if form.is_valid():
            bd = form.save(commit=False)
            bd.user = request.user

            # ── Razorpay: create/update Contact ─────────────────────────
            try:
                import razorpay
                rzp = razorpay.Client(
                    auth=(djsettings.RAZORPAY_KEY_ID, djsettings.RAZORPAY_KEY_SECRET)
                )
                contact_data = {
                    "name":         bd.account_holder,
                    "email":        request.user.email,
                    "contact":      profile.phone or "0000000000",
                    "type":         "employee" if profile.role == UserRole.EMPLOYEE else "vendor",
                    "reference_id": str(request.user.id),
                    "notes":        {"role": profile.role, "user_id": str(request.user.id)},
                }
                if bd.razorpay_contact_id:
                    # Update existing contact (PATCH not available in basic API — recreate)
                    contact = rzp.contact.create(data=contact_data)
                else:
                    contact = rzp.contact.create(data=contact_data)

                bd.razorpay_contact_id = contact["id"]

                # ── Create Fund Account ──────────────────────────────────
                fund_data = {
                    "contact_id":    contact["id"],
                    "account_type":  "bank_account",
                    "bank_account": {
                        "name":           bd.account_holder,
                        "ifsc":           bd.ifsc_code,
                        "account_number": bd.account_number,
                    },
                }
                fund_account = rzp.fund_account.create(data=fund_data)
                bd.razorpay_fund_account_id = fund_account["id"]
                bd.is_verified = False  # Razorpay validates async
                messages.success(request,
                    "✅ Bank details saved and Razorpay account created successfully!")

            except Exception as e:
                # Save bank details even if Razorpay API fails (test mode / network issue)
                messages.warning(request,
                    f"Bank details saved locally. Razorpay sync pending: {str(e)[:80]}")

            bd.save()

            # Redirect to appropriate profile/payments page
            if profile.role == UserRole.EMPLOYEE:
                return redirect("dashboard_employee_profile")
            return redirect("myprofile")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = BankDetailForm(instance=instance)

    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/bank_detail.html", {
        "form":         form,
        "bank_detail":  instance,
        "unread_count": unread,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN: Manage all bank accounts / Razorpay contacts
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def admin_bank_accounts(request):
    """Admin view: list all bank details, verify, delete, sync with Razorpay."""
    from django.conf import settings as djsettings
    from django.http import JsonResponse

    if not (request.user.is_superuser or
            ensure_profile(request.user).role == UserRole.ADMIN):
        return redirect("dashboard_admin_dashboard")

    bank_details = BankDetail.objects.select_related("user").order_by("-created_at")
    verified_count = bank_details.filter(is_verified=True).count()
    pending_count  = bank_details.filter(is_verified=False).count()
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "pages/dashboard/admin-bank-accounts.html", {
        "bank_details":    bank_details,
        "verified_count":  verified_count,
        "pending_count":   pending_count,
        "unread_count":    unread,
    })


@login_required
def admin_bank_verify(request, pk):
    """Admin: toggle verification status of a bank account."""
    from django.http import JsonResponse
    if not (request.user.is_superuser or
            ensure_profile(request.user).role == UserRole.ADMIN):
        return JsonResponse({"ok": False}, status=403)
    if request.method == "POST":
        bd = get_object_or_404(BankDetail, pk=pk)
        bd.is_verified = not bd.is_verified
        bd.save(update_fields=["is_verified"])
        return JsonResponse({"ok": True, "is_verified": bd.is_verified})
    return JsonResponse({"ok": False}, status=405)


@login_required
def admin_bank_delete(request, pk):
    """Admin: delete a bank account record."""
    from django.http import JsonResponse
    if not (request.user.is_superuser or
            ensure_profile(request.user).role == UserRole.ADMIN):
        return JsonResponse({"ok": False}, status=403)
    if request.method == "POST":
        bd = get_object_or_404(BankDetail, pk=pk)
        name = bd.account_holder
        bd.delete()
        messages.success(request, f"Bank account for {name} has been deleted.")
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False}, status=405)


@login_required
def dashboard_admin_settings(request):
    """Admin: Razorpay configuration + linked account overview."""
    from django.conf import settings as _cfg
    from pathlib import Path
    import razorpay as _rp

    if not is_admin(request.user):
        return redirect(_role_redirect(ensure_profile(request.user)))

    env_path   = Path(_cfg.BASE_DIR) / ".env"
    rzp_key    = _cfg.RAZORPAY_KEY_ID
    rzp_secret = _cfg.RAZORPAY_KEY_SECRET
    save_msg   = ""
    save_ok    = False
    test_msg   = ""
    test_ok    = False

    if request.method == "POST":
        action = request.POST.get("action", "save_keys")

        if action == "save_keys":
            new_key    = request.POST.get("rzp_key_id", "").strip()
            new_secret = request.POST.get("rzp_key_secret", "").strip()

            if new_key and new_secret:
                # Read existing .env with utf-8 (fixes Windows cp1252 UnicodeDecodeError)
                env_lines = []
                if env_path.exists():
                    try:
                        with open(env_path, encoding="utf-8") as f:
                            env_lines = f.readlines()
                    except UnicodeDecodeError:
                        # Fallback: read with errors='replace' then fix encoding
                        with open(env_path, encoding="utf-8", errors="replace") as f:
                            env_lines = f.readlines()

                key_set = secret_set = False
                new_lines = []
                for line in env_lines:
                    if line.startswith("RAZORPAY_KEY_ID="):
                        new_lines.append("RAZORPAY_KEY_ID=" + new_key + "\n")
                        key_set = True
                    elif line.startswith("RAZORPAY_KEY_SECRET="):
                        new_lines.append("RAZORPAY_KEY_SECRET=" + new_secret + "\n")
                        secret_set = True
                    else:
                        new_lines.append(line)
                if not key_set:
                    new_lines.append("RAZORPAY_KEY_ID=" + new_key + "\n")
                if not secret_set:
                    new_lines.append("RAZORPAY_KEY_SECRET=" + new_secret + "\n")

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

                import os
                os.environ["RAZORPAY_KEY_ID"]     = new_key
                os.environ["RAZORPAY_KEY_SECRET"]  = new_secret
                _cfg.RAZORPAY_KEY_ID     = new_key
                _cfg.RAZORPAY_KEY_SECRET = new_secret
                rzp_key    = new_key
                rzp_secret = new_secret
                save_ok    = True
                save_msg   = "✅ Keys saved to .env. Restart the server to fully apply."
            else:
                save_msg = "❌ Both Key ID and Key Secret are required."

        elif action == "test_keys":
            if rzp_key and rzp_secret:
                try:
                    client_rp = _rp.Client(auth=(rzp_key, rzp_secret))
                    client_rp.order.all({"count": 1})
                    test_ok  = True
                    test_msg = "✅ Razorpay connection successful! Keys are valid."
                except Exception as ex:
                    test_ok  = False
                    test_msg = f"❌ Connection failed: {str(ex)[:150]}"
            else:
                test_msg = "❌ Save keys first before testing."

    bank_details  = BankDetail.objects.select_related("user").order_by("-created_at")
    verified_cnt  = bank_details.filter(is_verified=True).count()
    pending_cnt   = bank_details.filter(is_verified=False, razorpay_fund_account_id="").count()
    unread        = Notification.objects.filter(user=request.user, is_read=False).count()

    masked_secret = ""
    if rzp_secret and len(rzp_secret) > 4:
        masked_secret = "*" * (len(rzp_secret) - 4) + rzp_secret[-4:]

    return render(request, "pages/dashboard/admin-settings.html", {
        "rzp_key":          rzp_key,
        "rzp_secret_masked": masked_secret,
        "rzp_configured":   bool(rzp_key and rzp_secret),
        "save_msg":         save_msg,
        "save_ok":          save_ok,
        "test_msg":         test_msg,
        "test_ok":          test_ok,
        "bank_details":     bank_details,
        "verified_cnt":     verified_cnt,
        "pending_cnt":      pending_cnt,
        "unread_notifications": unread,
    })


@login_required
def fix_payment_amount(request, payment_id):
    """Admin/Client: recalculate a PENDING payment amount from actual hours × rate."""
    from django.conf import settings as _cfg
    profile = ensure_profile(request.user)

    payment = get_object_or_404(Payment, id=payment_id)

    # Only allow the owning client or admin to recalculate
    if not (is_admin(request.user) or
            (profile.role == UserRole.CLIENT and payment.client.profile == profile)):
        return redirect("payments")

    if payment.status == PaymentStatus.PAID:
        messages.warning(request, "Cannot recalculate an already-paid payment.")
        return redirect("payments")

    task = payment.task
    _hours = task.total_hours or 0
    _rate  = task.employee.hourly_rate or 0
    if _hours and _rate:
        new_amount = float(_hours) * float(_rate)
        payment.amount = new_amount
        payment.save()
        messages.success(
            request,
            f"✅ Payment amount updated to ₹{new_amount:,.2f} "
            f"({_hours}h × ₹{_rate}/hr)"
        )
    else:
        messages.warning(request, "Cannot recalculate: task has no logged hours yet.")

    return redirect("payments")
