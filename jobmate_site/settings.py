from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Optional: loads .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me')
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages.apps.PagesConfig',
    'admin_app',
    'employee_app',
    'user_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jobmate_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'pages' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pages.context_processors.notifications_context',
                'pages.context_processors.user_avatar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'jobmate_site.wsgi.application'
ASGI_APPLICATION = 'jobmate_site.asgi.application'

# -----------------------------
# Database — PostgreSQL (required on all platforms including macOS)
# Install PostgreSQL: https://postgresapp.com (Mac) or postgresql.org (Windows/Linux)
# Set DB credentials in .env file
# -----------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     os.getenv("DB_NAME",     "jobmate_db"),
        "USER":     os.getenv("DB_USER",     "jobmate_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "your_pass"),
        "HOST":     os.getenv("DB_HOST",     "127.0.0.1"),
        "PORT":     os.getenv("DB_PORT",     "5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'dashboard_employee_dashboard'

# -----------------------------
# Email (Gmail SMTP)
# -----------------------------
# ── Email / Gmail SMTP ───────────────────────────────────────────
# To enable real email sending:
#   Step 1: Go to https://myaccount.google.com/security
#   Step 2: Enable 2-Step Verification
#   Step 3: Go to https://myaccount.google.com/apppasswords
#   Step 4: Create App Password → select "Mail" + "Windows Computer"
#   Step 5: Copy the 16-character password (no spaces) into EMAIL_HOST_PASSWORD in .env
#
# A valid Gmail App Password is exactly 16 lowercase letters (e.g. abcdwxyzefghijkl)
# Placeholder values like "your-gmail-app-password-here" are ignored → console mode

# ── Email / Gmail SMTP ───────────────────────────────────────────────────────
# Credentials are read from .env when available.
# Hardcoded fallbacks ensure email works on any machine even without a
# fully configured .env (e.g. when the project is copied to another Mac).
# To override, set EMAIL_HOST_USER / EMAIL_HOST_PASSWORD / ENQUIRY_RECIPIENT
# in your local .env file.

_DEFAULT_EMAIL_USER     = 'jobmate393@gmail.com'
_DEFAULT_EMAIL_PASSWORD = 'haebkdkgnirpplel'   # Gmail App Password (16 chars)
_DEFAULT_ENQUIRY_RCPT   = 'jobmate393@gmail.com'

# Gmail App Password — strip spaces (Google shows it as "xxxx xxxx xxxx xxxx")
_email_password_raw = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
_email_password_env = _email_password_raw.replace(' ', '')   # remove spaces → 16 chars
_email_user_env     = os.getenv('EMAIL_HOST_USER', '').strip()

# Decide whether the env-supplied password is a real 16-char App Password
def _is_real_password(pw: str) -> bool:
    return (
        len(pw) == 16
        and 'placeholder' not in pw.lower()
        and 'your-' not in pw.lower()
        and pw != ''
    )

# Use env value if valid, otherwise fall back to hardcoded credentials
if _is_real_password(_email_password_env) and _email_user_env:
    _email_password = _email_password_env
    _email_user     = _email_user_env
else:
    _email_password = _DEFAULT_EMAIL_PASSWORD
    _email_user     = _DEFAULT_EMAIL_USER

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = _email_user
EMAIL_HOST_PASSWORD = _email_password
DEFAULT_FROM_EMAIL  = _email_user

# Enquiry recipient: use env value if set and looks like an email, else default
_enquiry_env  = os.getenv('ENQUIRY_RECIPIENT', '').strip()
ENQUIRY_RECIPIENT = _enquiry_env if '@' in _enquiry_env else _DEFAULT_ENQUIRY_RCPT
# ── Razorpay ──────────────────────────────────────────────────
RAZORPAY_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')