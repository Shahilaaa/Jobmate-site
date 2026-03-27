"""
Standalone seed module — used by both 0001_squashed migration AND
the `python manage.py reseed` management command.
"""
from decimal import Decimal
import datetime


def run_seed():
    from django.utils import timezone
    from django.contrib.auth.models import User
    from pages.models import (
        Profile, EmployeeProfile, ClientProfile, Department, Skill,
        TaskRequest, WorkUpdate, Payment, PaymentStatus, TaskStatus,
        Project, ProjectStatus, ProjectApplication, ProjectApplicationStatus,
        ProjectPayment, SupportCard, FAQ, Testimonial, Notification,
        BankDetail, Accreditation, Portfolio
    )
    from datetime import timedelta

    now = timezone.now()

    # ════════════════════════════════════════════════════════
    # WIPE ALL EXISTING DATA
    # Use raw SQL TRUNCATE ... CASCADE to handle any FK constraints
    # including old tables (pages_bankaccount etc.) from previous migrations
    # ════════════════════════════════════════════════════════
    from django.db import connection
    with connection.cursor() as cursor:
        # Disable FK checks temporarily and truncate all pages_* tables
        cursor.execute("""
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename LIKE 'pages_%'
                )
                LOOP
                    EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                -- Also clear auth_user (but not Django system tables)
                TRUNCATE TABLE auth_user CASCADE;
            END $$;
        """)
    print("  ✓ All existing data wiped (TRUNCATE CASCADE)")

    # ════════════════════════════════════════════════════════
    # 20 DEPARTMENTS — each with 5 skills (categories)
    # ════════════════════════════════════════════════════════
    DEPT_DATA = [
        ("Software Development",   "Expert engineers for web, mobile, and backend development.",
         ["Web Development", "Mobile Development", "Backend Development", "Cloud & DevOps", "Software Testing / QA"]),
        ("UI/UX Design",           "Creative designers for interfaces and user experiences.",
         ["UI Design", "UX Research", "Figma / Sketch", "Prototyping", "Design Systems"]),
        ("Digital Marketing",      "Data-driven marketers to grow your online presence.",
         ["SEO", "Social Media Marketing", "Google Ads", "Email Marketing", "Content Marketing"]),
        ("Data & Analytics",       "Data professionals to turn raw data into insights.",
         ["Data Analysis", "Machine Learning", "Business Intelligence", "SQL", "Tableau / Power BI"]),
        ("IT Support",             "Reliable IT professionals to keep your systems running.",
         ["Network Administration", "Cybersecurity", "Cloud Computing", "DevOps", "Technical Support"]),
        ("Content Writing",        "Skilled writers for blogs, copy, and documentation.",
         ["Blog Writing", "Copywriting", "Technical Writing", "SEO Writing", "Content Strategy"]),
        ("Admin & Operations",     "Operations experts for day-to-day business management.",
         ["Project Management", "Virtual Assistance", "Bookkeeping", "Customer Support", "Data Entry"]),
        ("Finance & Accounting",   "Financial experts for accounting, tax, and planning.",
         ["Bookkeeping", "Financial Reporting", "Tax Preparation", "Payroll Processing", "Auditing"]),
        ("Human Resources",        "HR professionals for recruitment and employee management.",
         ["Recruitment", "Onboarding", "Employee Relations", "Performance Management", "HR Policy"]),
        ("Legal & Compliance",     "Legal experts for contracts, compliance, and governance.",
         ["Contract Drafting", "Intellectual Property", "Regulatory Compliance", "Labour Law", "Corporate Law"]),
        ("Engineering",            "Engineers for construction, mechanical, and civil projects.",
         ["Civil Engineering", "Mechanical Engineering", "Electrical Engineering", "CAD Design", "Project Supervision"]),
        ("Education & Training",   "Trainers and curriculum designers for learning programmes.",
         ["Corporate Training", "E-Learning Development", "Curriculum Design", "Academic Tutoring", "Workshop Facilitation"]),
        ("Healthcare & Medical",   "Medical professionals for healthcare IT and documentation.",
         ["Medical Transcription", "Healthcare IT", "Medical Coding", "Clinical Research", "Health Data Analysis"]),
        ("E-commerce",             "E-commerce specialists for online stores and marketplaces.",
         ["Product Listing", "Shopify Development", "Amazon / Flipkart", "Inventory Management", "Order Processing"]),
        ("Graphic Design",         "Visual designers for logos, branding, and marketing.",
         ["Logo Design", "Branding", "Print Design", "Packaging Design", "Illustration"]),
        ("Video & Media",          "Video editors and animators for digital content.",
         ["Video Editing", "Animation", "YouTube Management", "Podcast Production", "Motion Graphics"]),
        ("Customer Support",       "Support agents for live chat, email, and phone.",
         ["Live Chat Support", "Email Support", "Phone Support", "CRM Management", "Customer Success"]),
        ("Translation",            "Translators for Indian and global languages.",
         ["English to Hindi", "Hindi to English", "Tamil Translation", "Malayalam Translation", "Technical Translation"]),
        ("Research",               "Research analysts for market, academic, and data research.",
         ["Market Research", "Academic Research", "Competitive Analysis", "Survey Design", "Report Writing"]),
        ("Sales & Business Dev",   "Sales professionals for lead generation and growth.",
         ["Lead Generation", "Cold Outreach", "B2B Sales", "CRM / Salesforce", "Proposal Writing"]),
    ]

    depts = {}
    skills_map = {}
    for dept_name, desc, skill_names in DEPT_DATA:
        d = Department.objects.create(name=dept_name, description=desc)
        depts[dept_name] = d
        dept_skills = []
        for s in skill_names:
            skill = Skill.objects.create(department=d, name=s)
            dept_skills.append(skill)
        skills_map[dept_name] = dept_skills

    print(f"  ✓ {Department.objects.count()} departments created")
    print(f"  ✓ {Skill.objects.count()} skills (categories) created")

    # ════════════════════════════════════════════════════════
    # ADMIN USER
    # ════════════════════════════════════════════════════════
    admin_u = User.objects.create_superuser(
        username="admin@jobmate.com", email="admin@jobmate.com",
        password="Admin@1234", first_name="Admin", last_name="JobMate"
    )
    admin_prof = admin_u.profile
    admin_prof.role = "admin"; admin_prof.phone = "+91 90000 00001"; admin_prof.save()

    # ════════════════════════════════════════════════════════
    # 5 EMPLOYEES — one per key department
    # ════════════════════════════════════════════════════════
    EMP_DATA = [
        # first, last, email, phone, dept, skill_idx, hourly_rate, title
        ("Arjun",  "Nair",    "arjun.nair@jobmate.com",    "+91 91000 00001", "Software Development", 0, 2500, "Full-Stack Developer",       "I build scalable web and mobile applications with 4+ years of industry experience."),
        ("Priya",  "Menon",   "priya.menon@jobmate.com",   "+91 91000 00002", "UI/UX Design",         0, 2000, "UI/UX Designer",             "Creative designer with a passion for user-centered design and pixel-perfect interfaces."),
        ("Rahul",  "Sharma",  "rahul.sharma@jobmate.com",  "+91 91000 00003", "Digital Marketing",    0, 1500, "Digital Marketing Expert",   "SEO and performance marketing specialist who has scaled brands from 0 to 10k monthly visits."),
        ("Sneha",  "Pillai",  "sneha.pillai@jobmate.com",  "+91 91000 00004", "Data & Analytics",     0, 3000, "Data Analyst",               "Data-driven professional specialising in dashboards, ML models, and business intelligence."),
        ("Vikram", "Thomas",  "vikram.thomas@jobmate.com", "+91 91000 00005", "Content Writing",      0, 1200, "Senior Content Writer",      "Versatile writer with expertise in SEO blogs, technical docs, and brand storytelling."),
    ]
    employees = []
    for first, last, email, phone, dept_name, skill_idx, rate, title, bio in EMP_DATA:
        u = User.objects.create_user(username=email, email=email, password="Employee@1234",
                                      first_name=first, last_name=last)
        p = u.profile; p.role = "employee"; p.phone = phone; p.save()
        ClientProfile.objects.filter(profile=p).delete()
        emp = EmployeeProfile.objects.create(
            profile=p,
            department=depts[dept_name],
            skill=skills_map[dept_name][skill_idx],
            title=title, bio=bio,
            hourly_rate=Decimal(str(rate)),
            is_available=True,
            approval_status="approved",
            approved_at=now,
        )
        employees.append(emp)
        # 5 Portfolio items per employee
        for j in range(5):
            Portfolio.objects.create(
                employee=emp,
                title=f"{title} Project {j+1}",
                description=f"Delivered a high-impact {dept_name.lower()} project for a client.",
                date=(now - timedelta(days=30*j)).date(),
            )
        # 5 Accreditations per employee
        CERTS = [
            f"{dept_name} Professional Certification",
            "Google Analytics Certified",
            "Project Management Professional (PMP)",
            "Agile Scrum Master",
            "AWS Cloud Practitioner",
        ]
        for j, cert in enumerate(CERTS):
            Accreditation.objects.create(
                employee=emp, title=cert, issuer="Industry Body",
                date_issued=(now - timedelta(days=90*j)).date(),
            )

    print(f"  ✓ {EmployeeProfile.objects.count()} employees created")

    # ════════════════════════════════════════════════════════
    # 5 CLIENTS
    # ════════════════════════════════════════════════════════
    CLI_DATA = [
        ("Eva",    "Pillai",   "eva.pillai@jobmate.com",    "+91 92000 00001", "Pillai Digital Pvt Ltd"),
        ("Meena",  "Varghese", "meena.varghese@jobmate.com","+91 92000 00002", "Varghese Enterprises"),
        ("David",  "Nair",     "david.nair@jobmate.com",    "+91 92000 00003", "Nair Tech Solutions"),
        ("Anita",  "George",   "anita.george@jobmate.com",  "+91 92000 00004", "George & Co"),
        ("Suresh", "Kumar",    "suresh.kumar@jobmate.com",  "+91 92000 00005", "Kumar Startups"),
    ]
    clients = []
    for first, last, email, phone, company in CLI_DATA:
        u = User.objects.create_user(username=email, email=email, password="Client@1234",
                                      first_name=first, last_name=last)
        p = u.profile; p.role = "client"; p.phone = phone; p.save()
        cli = ClientProfile.objects.create(
            profile=p, company=company,
            approval_status="approved", approved_at=now
        )
        clients.append(cli)

    print(f"  ✓ {ClientProfile.objects.count()} clients created")

    # ════════════════════════════════════════════════════════
    # 5 TASKS PER CLIENT = 25 tasks total
    # Tasks 1-3: COMPLETED with payment (PAID)
    # Task 4:    SUBMITTED (payment pending)
    # Task 5:    IN_PROGRESS (no payment yet)
    # ════════════════════════════════════════════════════════
    TASK_TEMPLATES = [
        ("Website Redesign",         "Redesign the company website with modern UI and improved UX.",          employees[0], 5, 2500),
        ("SEO Audit & Optimisation", "Full SEO audit, keyword research, and on-page optimisation report.",    employees[2], 3, 1500),
        ("Sales Data Dashboard",     "Build an interactive Power BI dashboard for monthly sales data.",       employees[3], 4, 3000),
        ("Content Calendar Q1",      "Create a 3-month content calendar with 60 post ideas and copy.",       employees[4], 6, 1200),
        ("App UI Prototype",         "Design a high-fidelity Figma prototype for the mobile application.",   employees[1], 4, 2000),
    ]
    for cli in clients:
        for i, (title, desc, emp, hours, rate) in enumerate(TASK_TEMPLATES):
            if i < 3:
                status = TaskStatus.COMPLETED
            elif i == 3:
                status = TaskStatus.SUBMITTED
            else:
                status = TaskStatus.IN_PROGRESS

            task = TaskRequest.objects.create(
                client=cli, employee=emp,
                title=f"{title} — {cli.profile.user.first_name}",
                description=desc,
                department=emp.department, skill=emp.skill,
                budget=Decimal(str(rate)),
                status=status,
                start_date=(now - timedelta(days=30+i*3)).date(),
                end_date=(now - timedelta(days=i*3)).date(),
            )
            # Add work update for all non-pending
            WorkUpdate.objects.create(
                task=task, employee=emp,
                note=f"Completed all deliverables for {title}. See attached file.",
                hours_worked=Decimal(str(hours)),
                submitted_at=now - timedelta(days=i*2+1),
            )
            # Create PAID payment for completed tasks
            if status == TaskStatus.COMPLETED:
                amount = Decimal(str(hours)) * Decimal(str(rate))
                Payment.objects.create(
                    task=task, client=cli, amount=amount,
                    status=PaymentStatus.PAID,
                    method="razorpay",
                    transaction_id=f"TXN{cli.id:02d}{task.id:04d}",
                    paid_at=now - timedelta(days=i),
                )

    print(f"  ✓ {TaskRequest.objects.count()} tasks created")
    print(f"  ✓ {Payment.objects.filter(status='paid').count()} task payments (PAID)")

    # ════════════════════════════════════════════════════════
    # 5 PROJECTS PER CLIENT = 25 projects total
    # Projects 1-3: COMPLETED with PAID payment
    # Project 4:    WORK_SUBMITTED (payment pending)
    # Project 5:    ASSIGNED (in progress)
    # ════════════════════════════════════════════════════════
    PROJ_TEMPLATES = [
        ("E-commerce Platform Build",  "Build a complete e-commerce platform with Razorpay payment integration.", employees[0], 150000, ProjectStatus.COMPLETED),
        ("Brand Identity Package",     "Logo design, brand guidelines, business cards, and full collateral set.",  employees[1],  80000, ProjectStatus.COMPLETED),
        ("Q4 Marketing Campaign",      "Plan and execute full Q4 digital marketing campaign across 3 channels.",   employees[2],  60000, ProjectStatus.COMPLETED),
        ("Data Analytics Pipeline",    "Design and implement automated ETL pipeline with live Power BI reports.",  employees[3], 120000, ProjectStatus.WORK_SUBMITTED),
        ("Blog Content Package",       "Write 20 long-form SEO-optimised blog posts with meta descriptions.",      employees[4],  40000, ProjectStatus.ASSIGNED),
    ]
    for cli in clients:
        for i, (title, desc, emp, budget, status) in enumerate(PROJ_TEMPLATES):
            is_done = status == ProjectStatus.COMPLETED
            is_submitted = status == ProjectStatus.WORK_SUBMITTED
            proj = Project.objects.create(
                client=cli,
                title=f"{title} — {cli.profile.user.first_name}",
                description=desc,
                department=emp.department, skill=emp.skill,
                budget=Decimal(str(budget)),
                status=status,
                assigned_to=emp,
                deadline=now + timedelta(days=max(1, 30-i*5)),
                completed_at=now - timedelta(days=i*3) if is_done else None,
                work_note=f"All deliverables for {title} have been completed and handed over." if (is_done or is_submitted) else "",
            )
            ProjectApplication.objects.create(
                project=proj, employee=emp,
                status=ProjectApplicationStatus.ACCEPTED,
                message=f"I have extensive experience in {emp.title.lower()} and can deliver {title} on schedule.",
            )
            if is_done:
                ProjectPayment.objects.create(
                    project=proj, employee=emp, client=cli,
                    amount=Decimal(str(budget)),
                    status=PaymentStatus.PAID,
                    method="razorpay",
                    transaction_id=f"PTXN{cli.id:02d}{proj.id:04d}",
                )

    print(f"  ✓ {Project.objects.count()} projects created")
    print(f"  ✓ {ProjectPayment.objects.filter(status='paid').count()} project payments (PAID)")

    # ════════════════════════════════════════════════════════
    # 5 SUPPORT CARDS
    # ════════════════════════════════════════════════════════
    CARDS = [
        ("How It Works",       "Browse vetted professionals, post your task or project with a budget, get matched, and pay only when satisfied.", 0),
        ("Fast Turnaround",    "Most tasks are accepted within 24 hours. Professionals are available full-time and committed to your deadlines.", 1),
        ("Secure Payments",    "All payments go through Razorpay. Funds are released only after you mark the work as complete.", 2),
        ("Quality Guarantee",  "Every employee is vetted and rated. Request revisions or a redo at no extra cost if quality falls short.", 3),
        ("24/7 Support",       "Our support team is available around the clock. Raise a ticket anytime and get a response within one business day.", 4),
    ]
    for title, body, order in CARDS:
        SupportCard.objects.create(title=title, body=body, order=order)

    # ════════════════════════════════════════════════════════
    # 5 FAQs (plus 2 bonus)
    # ════════════════════════════════════════════════════════
    FAQS = [
        ("How do I post a task?",               "Go to Works → Add New Task, fill in the title, description, budget and deadline, then submit.", 0),
        ("How long to find an employee?",        "Most tasks are matched within 24–48 hours depending on skill and availability.", 1),
        ("Can I chat with my employee?",          "Yes — a direct chat opens automatically once a task is accepted.", 2),
        ("How do I make a payment?",              "Click Pay Now on the Payments page after the task is completed. Razorpay handles the checkout securely.", 3),
        ("How is the payment split?",             "80% goes to the employee, 20% is the platform commission. Both amounts are shown clearly before you pay.", 4),
        ("Can I cancel a task?",                  "Yes — tasks in Pending status can be deleted. Accepted tasks require agreement from both parties to cancel.", 5),
        ("How do projects differ from tasks?",   "Tasks are simpler one-off jobs. Projects are longer engagements with a fixed client-agreed budget.", 6),
    ]
    for q, a, order in FAQS:
        FAQ.objects.create(question=q, answer=a, order=order)

    # ════════════════════════════════════════════════════════
    # 5 TESTIMONIALS for each employee (25 total)
    # ════════════════════════════════════════════════════════
    TESTI_DATA = [
        ("Meena Varghese",  "CEO, Varghese Enterprises",  5, "Delivered everything on time and exceeded expectations. Highly recommended!"),
        ("David Nair",      "CTO, Nair Tech Solutions",   5, "Excellent work quality and proactive communication throughout the project."),
        ("Anita George",    "MD, George & Co",            5, "Professional, reliable, and creative. Will definitely hire again."),
        ("Suresh Kumar",    "Founder, Kumar Startups",    5, "Turned our idea into a polished product. Outstanding quality and fast delivery."),
        ("Eva Pillai",      "Director, Pillai Digital",   4, "Great attention to detail and fast turnaround. Our best hire on this platform."),
    ]
    for emp in employees:
        for author, title_t, rating, text in TESTI_DATA:
            Testimonial.objects.create(
                employee=emp, author_name=author, author_title=title_t,
                text=text, rating=rating,
                date=datetime.date.today(),
                show_on_homepage=True,
            )

    print(f"  ✓ {Testimonial.objects.count()} testimonials created")
    print(f"  ✓ {SupportCard.objects.count()} support cards, {FAQ.objects.count()} FAQs")
    print()
    print("  Logins:")
    print("    Admin:    admin@jobmate.com      / Admin@1234")
    print("    Employee: arjun.nair@jobmate.com / Employee@1234")
    print("    Client:   eva.pillai@jobmate.com / Client@1234")
