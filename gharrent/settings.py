"""
Django settings for gharrent project.
"""

from pathlib import Path
from decouple import config
from dotenv import load_dotenv
from django.contrib.messages import constants as messages

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the project .env file before reading config values
load_dotenv(BASE_DIR / ".env")


# ==================================================
# SECURITY
# ==================================================

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-this-in-production")

DEBUG = config("DEBUG", default=False, cast=bool)


# ==================================================
# HOSTS
# ==================================================

ALLOWED_HOSTS = [
    "ghrrent.onrender.com",
    "localhost",
    "127.0.0.1",
]


# ==================================================
# APPLICATIONS
# ==================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]


# ==================================================
# MIDDLEWARE
# ==================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "gharrent.urls"


# ==================================================
# TEMPLATES
# ==================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "gharrent.wsgi.application"


# ==================================================
# DATABASE
# ==================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==================================================
# PASSWORD VALIDATION
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ==================================================
# INTERNATIONALIZATION
# ==================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True


# ==================================================
# STATIC FILES
# ==================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ==================================================
# MEDIA FILES
# ==================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================================================
# EMAIL CONFIGURATION
# ==================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")

EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)

EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)

EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")

EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@gharrent.com")

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")

GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")

# Production: Set GOOGLE_REDIRECT_URI in environment (e.g., https://ghrrent.onrender.com/gmail/callback/)
# Development: Defaults to http://127.0.0.1:8000/gmail/callback/
GOOGLE_REDIRECT_URI = config(
    "GOOGLE_REDIRECT_URI",
    default="http://127.0.0.1:8000/gmail/callback/",
)


# ==================================================
# AUTHENTICATION
# ==================================================

LOGIN_URL = "core:login"

LOGIN_REDIRECT_URL = "core:dashboard"

LOGOUT_REDIRECT_URL = "core:login"


# ==================================================
# CSRF
# ==================================================

CSRF_TRUSTED_ORIGINS = [
    "https://ghrrent.onrender.com",
]

# Support local development
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(
        [
            "http://localhost",
            "http://127.0.0.1",
        ]
    )


# ==================================================
# MESSAGE TAGS
# ==================================================

MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}


# ==================================================
# SECURITY - HTTPS/SSL (for Render)
# ==================================================

# Render automatically sets X-Forwarded-Proto header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# In production, enforce HTTPS
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False  # Render handles redirects at the platform level
