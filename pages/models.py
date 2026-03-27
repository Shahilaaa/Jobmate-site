from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class Department(models.Model):
    name        = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")
    image       = models.ImageField(upload_to="departments/", blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Skill(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("department", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.department.name})"


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    EMPLOYEE = "employee", "Employee"
    CLIENT = "client", "Client"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CLIENT)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)  # user profile bio

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class ApprovalStatus(models.TextChoices):
    PENDING  = "pending",  "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class EmployeeProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="employee")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    background_image = models.ImageField(upload_to="backgrounds/", blank=True, null=True)
    cv = models.FileField(upload_to="cvs/", blank=True, null=True)
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Employee: {self.profile.user.get_full_name() or self.profile.user.username}"


class ClientProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="client")
    company = models.CharField(max_length=160, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    background_image = models.ImageField(upload_to="backgrounds/", blank=True, null=True)
    national_id = models.FileField(upload_to="national_ids/", blank=True, null=True)
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Client: {self.profile.user.get_full_name() or self.profile.user.username}"


class Testimonial(models.Model):
    employee = models.ForeignKey(
        "EmployeeProfile", on_delete=models.CASCADE, related_name="testimonials"
    )
    author_name = models.CharField(max_length=120)
    author_title = models.CharField(max_length=120, blank=True)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5, help_text="1–5 stars")
    author_image = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    date = models.DateField()
    show_on_homepage = models.BooleanField(default=True, help_text="Show on the public homepage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Testimonial by {self.author_name} for {self.employee}"


class Accreditation(models.Model):
    employee = models.ForeignKey(
        "EmployeeProfile", on_delete=models.CASCADE, related_name="accreditations"
    )
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="accreditations/", blank=True, null=True)
    date_issued = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_issued"]

    def __str__(self):
        return f"{self.title} — {self.employee}"


class Portfolio(models.Model):
    employee    = models.ForeignKey(
        "EmployeeProfile", on_delete=models.CASCADE, related_name="portfolio_items"
    )
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link        = models.URLField(blank=True, help_text="Live project or demo URL")
    image       = models.ImageField(upload_to="portfolio/", blank=True, null=True)
    date        = models.DateField(blank=True, null=True, help_text="Project completion date")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} — {self.employee}"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In Progress"
    SUBMITTED = "submitted", "Submitted"
    COMPLETED = "completed", "Completed"
    REJECTED = "rejected", "Rejected"


class TaskRequest(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="tasks")
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name="tasks")

    title = models.CharField(max_length=160)
    description = models.TextField()

    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)

    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    @property
    def total_hours(self):
        agg = self.work_updates.aggregate(total=Sum("hours_worked"))
        return agg["total"] or 0

    @property
    def estimated_cost(self):
        # automatic cost detection based on employee hourly rate and logged hours
        return (self.total_hours or 0) * (self.employee.hourly_rate or 0)


class WorkUpdate(models.Model):
    task = models.ForeignKey(TaskRequest, on_delete=models.CASCADE, related_name="work_updates")
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)

    note = models.TextField(blank=True)
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    attachment = models.FileField(upload_to="work/", blank=True, null=True)
    work_file = models.FileField(
        upload_to="work_deliverables/",
        blank=True,
        null=True,
        help_text="Final deliverable file for the client to download"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Update for {self.task_id} ({self.hours_worked}h)"

    def get_work_file_name(self):
        if self.work_file:
            return self.work_file.name.split('/')[-1]
        return None


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"


class Payment(models.Model):
    task = models.OneToOneField(TaskRequest, on_delete=models.CASCADE, related_name="payment")
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    admin_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0,
        help_text="20% of amount kept by admin")
    employee_payout = models.DecimalField(max_digits=12, decimal_places=2, default=0,
        help_text="80% of amount transferred to employee")
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True,
        help_text="Razorpay payment reference")
    razorpay_order_id   = models.CharField(max_length=64, blank=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True)
    razorpay_signature  = models.CharField(max_length=128, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.amount:
            from decimal import Decimal
            self.admin_commission = round(Decimal(str(self.amount)) * Decimal("0.20"), 2)
            self.employee_payout  = round(Decimal(str(self.amount)) * Decimal("0.80"), 2)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Payment {self.id} ({self.status})"


class TicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    CLOSED = "closed", "Closed"


class SupportTicket(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=160)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.subject} ({self.status})"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True)  # URL to navigate when clicked
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({'read' if self.is_read else 'unread'})"


class Conversation(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='conversations')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'employee')

    def __str__(self) -> str:
        return f"Chat {self.client_id}-{self.employee_id}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Msg {self.id} by {self.sender_id}"

    def attachment_name(self):
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return None

    def is_image(self):
        if self.attachment:
            name = self.attachment.name.lower()
            return any(name.endswith(ext) for ext in ['.jpg','.jpeg','.png','.gif','.webp','.bmp'])


class Enquiry(models.Model):
    name       = models.CharField(max_length=120)
    email      = models.EmailField()
    service    = models.CharField(max_length=120, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"Enquiry from {self.name} ({self.email})"
        return False

# ── Support Page Content ──────────────────────────────────────────────────────

class SupportCard(models.Model):
    """The 3 info cards shown at the top of the Support page."""
    title   = models.CharField(max_length=120)
    body    = models.TextField()
    order   = models.PositiveSmallIntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """Accordion FAQ items on the Support page."""
    question   = models.CharField(max_length=300)
    answer     = models.TextField()
    order      = models.PositiveSmallIntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question[:80]


# ── Project Feature ───────────────────────────────────────────────────────────

class ProjectStatus(models.TextChoices):
    ACTIVE           = "active",           "Active"
    ASSIGNED         = "assigned",         "Assigned"
    WORK_SUBMITTED   = "work_submitted",   "Work Submitted"
    COMPLETED        = "completed",        "Completed"
    CLOSED           = "closed",           "Closed"


class ProjectApplicationStatus(models.TextChoices):
    PENDING  = "pending",  "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Project(models.Model):
    client      = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="projects")
    title       = models.CharField(max_length=200)
    description = models.TextField()
    department  = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    skill       = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
    budget      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline    = models.DateTimeField(null=True, blank=True,
                    help_text="Exact deadline. Use date+time when due within 24 h.")
    status           = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    assigned_to      = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_projects")
    work_file        = models.FileField(upload_to="project_deliverables/", blank=True, null=True)
    work_note        = models.TextField(blank=True)
    work_submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def get_work_file_name(self):
        if self.work_file:
            return self.work_file.name.split("/")[-1]
        return None

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class ProjectApplication(models.Model):
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="applications")
    employee   = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name="project_applications")
    message    = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=ProjectApplicationStatus.choices, default=ProjectApplicationStatus.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "employee")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.employee} → {self.project.title} ({self.status})"


class ProjectPayment(models.Model):
    """Revenue record created when a client marks a project as complete."""
    project    = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="payment")
    employee   = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name="project_payments")
    client     = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="project_payments")
    amount     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    admin_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0,
        help_text="20% of amount kept by admin")
    employee_payout  = models.DecimalField(max_digits=12, decimal_places=2, default=0,
        help_text="80% of amount transferred to employee")
    status     = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    method     = models.CharField(max_length=50, blank=True)
    transaction_id   = models.CharField(max_length=100, blank=True)
    razorpay_order_id   = models.CharField(max_length=64, blank=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True)
    razorpay_signature  = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.amount:
            from decimal import Decimal
            self.admin_commission = round(Decimal(str(self.amount)) * Decimal("0.20"), 2)
            self.employee_payout  = round(Decimal(str(self.amount)) * Decimal("0.80"), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ProjectPayment #{self.id} — {self.project.title} (₹{self.amount})"


class AccountType(models.TextChoices):
    SAVINGS = "savings", "Savings"
    CURRENT = "current", "Current"


class BankDetail(models.Model):
    """Bank account details for employees and clients — used to create Razorpay contacts."""
    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bank_detail")
    account_holder   = models.CharField(max_length=160)
    account_number   = models.CharField(max_length=30)
    ifsc_code        = models.CharField(max_length=20)
    bank_name        = models.CharField(max_length=120)
    branch_name      = models.CharField(max_length=160, blank=True)
    account_type     = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.SAVINGS)
    # Razorpay IDs (auto-populated when account created in Razorpay)
    razorpay_contact_id      = models.CharField(max_length=64, blank=True)
    razorpay_fund_account_id = models.CharField(max_length=64, blank=True)
    is_verified      = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.bank_name}"
