from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Enquiry,
    ClientProfile,
    Department,
    EmployeeProfile,
    FAQ,
    Payment,
    Profile,
    Skill,
    SupportCard,
    SupportTicket,
    TaskRequest,
    Testimonial,
    WorkUpdate,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ("name", "description_short", "image")
    search_fields = ("name", "description")

    def description_short(self, obj):
        return obj.description[:80] + "…" if len(obj.description) > 80 else obj.description
    description_short.short_description = "Description"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_filter = ("department",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(EmployeeProfile)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("profile", "department", "skill", "hourly_rate", "is_available")
    list_filter = ("department", "skill", "is_available")
    search_fields = ("profile__user__username", "profile__user__email")


@admin.register(ClientProfile)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("profile", "company")
    search_fields = ("profile__user__username", "profile__user__email", "company")


@admin.register(TaskRequest)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "employee", "status", "budget", "created_at")
    list_filter = ("status", "department", "skill")
    search_fields = ("title", "client__profile__user__username", "employee__profile__user__username")


@admin.register(WorkUpdate)
class WorkUpdateAdmin(admin.ModelAdmin):
    list_display = ("task", "employee", "hours_worked", "submitted_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("task", "client", "amount", "status", "paid_at")
    list_filter = ("status",)


@admin.register(SupportTicket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_by", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("subject", "created_by__username")


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "service", "created_at")
    search_fields = ("name", "email", "service")


# ── Testimonial ───────────────────────────────────────────────────────────────

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display  = ("author_name", "author_title", "rating_stars", "date", "show_on_homepage", "employee", "preview_image")
    list_editable = ("show_on_homepage",)
    list_filter   = ("show_on_homepage", "rating")
    search_fields = ("author_name", "author_title", "text")
    ordering      = ("-date",)

    def rating_stars(self, obj):
        filled = "★" * obj.rating
        empty  = "☆" * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b;font-size:16px;">{}</span>'
                           '<span style="color:#ccc;font-size:16px;">{}</span>', filled, empty)
    rating_stars.short_description = "Rating"

    def preview_image(self, obj):
        if obj.author_image:
            return format_html('<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;">', obj.author_image.url)
        return "—"
    preview_image.short_description = "Photo"


# ── Support Content ───────────────────────────────────────────────────────────

@admin.register(SupportCard)
class SupportCardAdmin(admin.ModelAdmin):
    list_display  = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "body")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display  = ("question_short", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question", "answer")

    def question_short(self, obj):
        return obj.question[:80]
    question_short.short_description = "Question"

# ── Project feature ──────────────────────────────────────────────────────────
from .models import Project, ProjectApplication, BankDetail

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'status', 'budget', 'deadline', 'created_at']
    list_filter  = ['status']
    search_fields = ['title', 'description']

@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ['project', 'employee', 'status', 'applied_at']
    list_filter  = ['status']

from .models import ProjectPayment as _ProjectPayment

@admin.register(_ProjectPayment)
class ProjectPaymentAdmin(admin.ModelAdmin):
    list_display = ['project', 'employee', 'client', 'amount', 'status', 'created_at']
    list_filter  = ['status']

@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display  = ['user', 'account_holder', 'bank_name', 'ifsc_code', 'account_type', 'is_verified', 'razorpay_contact_id', 'created_at']
    list_filter   = ['is_verified', 'account_type']
    search_fields = ['user__username', 'user__email', 'account_holder', 'bank_name', 'ifsc_code']
    list_editable = ['is_verified']
    readonly_fields = ['razorpay_contact_id', 'razorpay_fund_account_id', 'created_at', 'updated_at']
