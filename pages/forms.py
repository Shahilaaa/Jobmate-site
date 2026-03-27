from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import (
    ClientProfile,
    Department,
    EmployeeProfile,
    Profile,
    Skill,
    SupportTicket,
    TaskRequest,
    ChatMessage,
    UserRole,
    WorkUpdate,
    Testimonial,
    Accreditation,
    BankDetail,
)


class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)

    register_type = forms.ChoiceField(
        choices=(
            (UserRole.CLIENT, "Client"),
            (UserRole.EMPLOYEE, "Employee"),
        )
    )

    # Employee-only fields
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    skill = forms.ModelChoiceField(queryset=Skill.objects.select_related("department").all(), required=False)
    cv = forms.FileField(required=False)

    # Client-only fields
    company = forms.CharField(max_length=160, required=False)
    national_id = forms.FileField(required=False)

    password = forms.CharField(widget=forms.PasswordInput)
    retype_password = forms.CharField(widget=forms.PasswordInput)

    profile_image = forms.ImageField(required=False)

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password", "")
        rpw = cleaned.get("retype_password", "")
        if pw and rpw and pw != rpw:
            raise forms.ValidationError("Passwords do not match")
        email = cleaned.get("email", "")
        if email and User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists")
        role = cleaned.get("register_type", "")
        if role == UserRole.EMPLOYEE:
            if not cleaned.get("department"):
                raise forms.ValidationError("Please select a Department")
            dept = cleaned.get("department")
            if dept and dept.skills.exists() and not cleaned.get("skill"):
                raise forms.ValidationError("Please select a Skill / Category")
            if not cleaned.get("cv"):
                raise forms.ValidationError("CV / Resume upload is required for Employee registration")
        elif role == UserRole.CLIENT:
            if not cleaned.get("national_id"):
                raise forms.ValidationError("National ID document upload is required for Client registration")
        return cleaned

    def save(self) -> User:
        full_name = self.cleaned_data["full_name"].strip()
        first_name = full_name.split(" ", 1)[0]
        last_name = full_name.split(" ", 1)[1] if " " in full_name else ""

        user = User.objects.create_user(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=first_name,
            last_name=last_name,
        )

        profile = user.profile
        profile.phone = self.cleaned_data.get("phone", "")
        role = self.cleaned_data["register_type"]
        if role not in (UserRole.CLIENT, UserRole.EMPLOYEE):
            role = UserRole.CLIENT
        profile.role = role
        profile.save()

        if role == UserRole.EMPLOYEE:
            # Delete any ClientProfile the signal may have auto-created for this profile
            ClientProfile.objects.filter(profile=profile).delete()
            emp, _ = EmployeeProfile.objects.get_or_create(profile=profile)
            emp.department = self.cleaned_data.get("department")
            emp.skill = self.cleaned_data.get("skill")
            emp.title = self.cleaned_data.get("skill").name if self.cleaned_data.get("skill") else ""
            if self.cleaned_data.get("cv"):
                emp.cv = self.cleaned_data["cv"]
            if self.cleaned_data.get("profile_image"):
                emp.profile_image = self.cleaned_data["profile_image"]
            emp.save()
        else:
            # Use get_or_create so signal pre-creation doesn't cause IntegrityError
            client, _ = ClientProfile.objects.get_or_create(profile=profile)
            client.company = self.cleaned_data.get("company", "")
            if self.cleaned_data.get("national_id"):
                client.national_id = self.cleaned_data["national_id"]
            if self.cleaned_data.get("profile_image"):
                client.profile_image = self.cleaned_data["profile_image"]
            client.save()

        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        user = authenticate(username=cleaned.get("email"), password=cleaned.get("password"))
        if not user:
            raise forms.ValidationError("Invalid email or password")
        cleaned["user"] = user
        return cleaned


class TaskRequestForm(forms.ModelForm):
    class Meta:
        model = TaskRequest
        fields = ["employee", "title", "description", "department", "skill", "start_date", "end_date"]
        # budget is intentionally excluded — it is auto-set from the employee's hourly_rate


class WorkUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkUpdate
        fields = ["note", "hours_worked", "attachment", "work_file"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 5, "style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:6px;outline:none;font-family:inherit;resize:vertical;", "placeholder": "Describe work done, what was completed, any notes for the client..."}),
            "hours_worked": forms.NumberInput(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:6px;outline:none;", "step": "0.5", "min": "0"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['work_file'].help_text = "Upload the final deliverable file for the client to download (PDF, ZIP, images, etc.)"
        self.fields['attachment'].help_text = "Optional internal attachment (screenshots, references)"


class TicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["subject", "message"]


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Profile
        fields = ["phone", "bio"]
        widgets = {
            "phone": forms.TextInput(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:2px;outline:none;font-family:inherit;"}),
            "bio": forms.Textarea(attrs={"rows": 6, "style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:2px;outline:none;font-family:inherit;resize:vertical;"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        base = "width:100%; padding:10px 12px; border:1px solid #e0e0e0; border-radius:2px; outline:none; font-family:inherit;"
        self.fields["first_name"].widget.attrs["style"] = base
        self.fields["last_name"].widget.attrs["style"] = base
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if getattr(self, "_user", None):
            self._user.first_name = self.cleaned_data.get("first_name", "")
            self._user.last_name = self.cleaned_data.get("last_name", "")
            if commit:
                self._user.save()
        return profile


class EmployeeProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ["department", "skill", "title", "bio", "hourly_rate", "is_available", "profile_image", "background_image"]
        widgets = {
            "title": forms.TextInput(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:4px;outline:none;font-family:inherit;"}),
            "bio": forms.Textarea(attrs={"rows": 4, "style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:4px;outline:none;font-family:inherit;resize:vertical;"}),
            "hourly_rate": forms.NumberInput(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:4px;outline:none;", "step": "0.01", "min": "0"}),
            "department": forms.Select(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:4px;outline:none;"}),
            "skill": forms.Select(attrs={"style": "width:100%;padding:10px 12px;border:1px solid #e0e0e0;border-radius:4px;outline:none;"}),
        }


class ClientProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ["company", "profile_image", "background_image"]
        widgets = {
            "company": forms.TextInput(attrs={"style": "width:100%;padding:10px;border:1px solid #e0e0e0;border-radius:4px;"}),
        }




class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["author_name", "author_title", "text", "rating", "author_image", "date"]
        widgets = {
            "author_name": forms.TextInput(attrs={"style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;", "placeholder": "Client or colleague name"}),
            "author_title": forms.TextInput(attrs={"style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;", "placeholder": "Their title or company (optional)"}),
            "text": forms.Textarea(attrs={"rows": 3, "style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;resize:vertical;", "placeholder": "What they said about your work..."}),
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "style": "width:80px;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;"}),
            "date": forms.DateInput(attrs={"type": "date", "style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;"}),
        }


class AccreditationForm(forms.ModelForm):
    class Meta:
        model = Accreditation
        fields = ["title", "issuer", "image", "date_issued"]
        widgets = {
            "title": forms.TextInput(attrs={"style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;", "placeholder": "Certificate or award title"}),
            "issuer": forms.TextInput(attrs={"style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;", "placeholder": "Issuing organization (optional)"}),
            "date_issued": forms.DateInput(attrs={"type": "date", "style": "width:100%;padding:9px 12px;border:1px solid #e0e0e0;border-radius:6px;font-family:inherit;font-size:13px;"}),
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["text", "attachment"]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Type a message...",
                "style": "width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-family:inherit;font-size:14px;resize:none;outline:none;",
                "id": "chatTextInput",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        text = cleaned.get("text", "").strip()
        attachment = cleaned.get("attachment")
        if not text and not attachment:
            raise forms.ValidationError("Please enter a message or attach a file.")
        return cleaned


_field_style = "width:100%;padding:10px 13px;border:1.5px solid #C5D8F0;border-radius:8px;font-size:14px;font-family:inherit;outline:none;background:#F8FBFF;"
_sel_style   = _field_style + "cursor:pointer;"

class BankDetailForm(forms.ModelForm):
    class Meta:
        model  = BankDetail
        fields = ["account_holder", "account_number", "ifsc_code",
                  "bank_name", "branch_name", "account_type"]
        widgets = {
            "account_holder": forms.TextInput(attrs={"style": _field_style, "placeholder": "Full name as on bank account"}),
            "account_number": forms.TextInput(attrs={"style": _field_style, "placeholder": "Bank account number"}),
            "ifsc_code":      forms.TextInput(attrs={"style": _field_style, "placeholder": "e.g. SBIN0001234", "maxlength": "11"}),
            "bank_name":      forms.TextInput(attrs={"style": _field_style, "placeholder": "e.g. State Bank of India"}),
            "branch_name":    forms.TextInput(attrs={"style": _field_style, "placeholder": "Branch name (optional)"}),
            "account_type":   forms.Select(attrs={"style": _sel_style}),
        }

    def clean_ifsc_code(self):
        v = self.cleaned_data.get("ifsc_code", "").strip().upper()
        if v and len(v) != 11:
            raise forms.ValidationError("IFSC code must be exactly 11 characters.")
        return v

    def clean_account_number(self):
        v = self.cleaned_data.get("account_number", "").strip()
        if not v.isdigit():
            raise forms.ValidationError("Account number must contain digits only.")
        return v
