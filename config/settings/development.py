"""Development settings."""
from .base import *  # noqa

DEBUG = True

# Use SQLite for quick local dev if no DATABASE_URL is set
# Override in .env with DATABASE_URL=postgres://... for Postgres

# Show emails in console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional — install separately)
# INSTALLED_APPS += ["debug_toolbar"]
