"""
Production settings — used on Render.com.
All secrets come from environment variables; nothing is hardcoded.
"""
from .base import *  # noqa
import dj_database_url
import os

DEBUG = False

# ─── Hosts ────────────────────────────────────────────────────────────────────
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
_allowed = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
if RENDER_HOSTNAME and RENDER_HOSTNAME not in _allowed:
    _allowed.append(RENDER_HOSTNAME)
# Always allow the known Render hostname
_allowed.append("grantbridge-backend-2.onrender.com")
ALLOWED_HOSTS = list(set(_allowed))

# ─── Database ─────────────────────────────────────────────────────────────────
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
    # Fallback to SQLite if DATABASE_URL not set (should not happen in prod)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files — served from /media/ in dev; use cloud storage in production
# For Render free tier, media is stored on the ephemeral disk.
# For persistent storage, swap to S3/Cloudinary (see README).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Security ─────────────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["https://grantbridge.vercel.app"],
)
CORS_ALLOW_CREDENTIALS = True

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="GrantBridge <noreply@grantbridge.com>",
)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
