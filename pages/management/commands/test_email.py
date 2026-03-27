"""
Management command to test email configuration.
Run: python manage.py test_email
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


class Command(BaseCommand):
    help = "Test email configuration — sends a test email to ENQUIRY_RECIPIENT"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*55)
        self.stdout.write("  JobMate Email Configuration Test")
        self.stdout.write("="*55)

        # Show current config
        backend = settings.EMAIL_BACKEND
        host    = getattr(settings, "EMAIL_HOST", "—")
        user    = getattr(settings, "EMAIL_HOST_USER", "—")
        pwd     = getattr(settings, "EMAIL_HOST_PASSWORD", "")
        recip   = getattr(settings, "ENQUIRY_RECIPIENT", "—")

        self.stdout.write(f"\n  Backend  : {backend.split('.')[-1]}")
        self.stdout.write(f"  Host     : {host}:{getattr(settings,'EMAIL_PORT',587)}")
        self.stdout.write(f"  Username : {user}")
        self.stdout.write(f"  Password : {'*' * len(pwd) if pwd else '(not set)'}")
        self.stdout.write(f"  Send to  : {recip}\n")

        if "console" in backend.lower():
            self.stdout.write(self.style.WARNING(
                "⚠  Console backend active — emails print here, NOT sent.\n"
                "   To enable real email:\n"
                "   1. Go to https://myaccount.google.com/apppasswords\n"
                "   2. Create an App Password (16 chars, no spaces)\n"
                "   3. Set EMAIL_HOST_PASSWORD=<your-16-char-password> in .env\n"
                "   4. Restart the server\n"
            ))
            return

        self.stdout.write("  Sending test email...")
        try:
            plain = (
                "This is a test email from the JobMate enquiry system.\n\n"
                "If you received this, email is configured correctly!\n\n"
                "— JobMate"
            )
            html = """<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:32px;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;box-shadow:0 4px 20px rgba(0,0,0,.1);">
  <div style="text-align:center;margin-bottom:24px;">
    <div style="font-size:48px;">✅</div>
    <h2 style="color:#166534;margin:12px 0 6px;">Email is working!</h2>
    <p style="color:#555;font-size:14px;margin:0;">JobMate enquiry emails are configured correctly.</p>
  </div>
  <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;text-align:center;">
    <p style="margin:0;font-size:13px;color:#166534;">Enquiry form submissions will be delivered to this inbox.</p>
  </div>
</div>
</body></html>"""
            msg = EmailMultiAlternatives(
                subject="✅ JobMate Email Test — Working!",
                body=plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recip],
            )
            msg.attach_alternative(html, "text/html")
            msg.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(
                f"\n  ✅ SUCCESS! Test email sent to {recip}\n"
                f"     Check your inbox (also check Spam folder).\n"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n  ❌ FAILED: {e}\n\n"
                "  Common fixes:\n"
                "  • Make sure 2-Step Verification is ON at myaccount.google.com/security\n"
                "  • Generate App Password at myaccount.google.com/apppasswords\n"
                "  • App Password must be exactly 16 characters, no spaces\n"
                "  • Do NOT use your regular Gmail password\n"
                "  • Copy it exactly into EMAIL_HOST_PASSWORD in .env\n"
                "  • Restart the Django server after editing .env\n"
            ))
        self.stdout.write("="*55 + "\n")
