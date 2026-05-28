"""
Production settings — Render.com deployment.
All secrets from environment variables. Nothing hardcoded.
"""
from .base import *  # noqa
import dj_database_url
import os

DEBUG = False

# ─── Hosts ────────────────────────────────────────────────────────────────────
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".onrender.com", "grantbridge-backend-2.onrender.com"]
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

# ─── Database (PostgreSQL via Render) ─────────────────────────────────────────
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=_db_url.startswith("postgres"),
        )
    }
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }

# ─── Static files (WhiteNoise) ────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = False
WHITENOISE_AUTOREFRESH = False

# ─── Media files (Cloudinary for persistent storage) ─────────────────────────
_cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if _cloudinary_url:
    import cloudinary
    cloudinary.config(cloudinary_url=_cloudinary_url)
    INSTALLED_APPS = INSTALLED_APPS + ["cloudinary_storage", "cloudinary"]  # type: ignore
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    MEDIA_URL = "/media/"
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# ─── REST Framework — JSON only, no browsable API ────────────────────────────
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # type: ignore
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ),
}

# ─── Security ─────────────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = False          # Render proxy handles SSL
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "https://grantbridge-frontend.vercel.app")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ─── Email — Gmail SMTP port 465 SSL (confirmed working) ─────────────────────
_sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")

if _sendgrid_key:
    # Use SendGrid if key is available and sender is verified
    INSTALLED_APPS = INSTALLED_APPS + ["anymail"]  # type: ignore
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {"SENDGRID_API_KEY": _sendgrid_key}
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "GrantBridge <suzywizzy6@gmail.com>")
else:
    # Gmail SMTP port 465 SSL — works on Render
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 465
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
    EMAIL_TIMEOUT = 10
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "GrantBridge <suzywizzy6@gmail.com>")

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "anymail": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}