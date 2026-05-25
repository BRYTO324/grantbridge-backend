"""Development settings."""
from .base import *  # noqa

DEBUG = True

# Use SQLite for quick local dev if no DATABASE_URL is set
# Override in .env with DATABASE_URL=postgres://... for Postgres

# Email backend is read from .env — set EMAIL_BACKEND there.
# Use smtp.EmailBackend + Gmail App Password to send real emails.
# Use console.EmailBackend to print emails to terminal instead.

# Relax CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional — install separately)
# INSTALLED_APPS += ["debug_toolbar"]
