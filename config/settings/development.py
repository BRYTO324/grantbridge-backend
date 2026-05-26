"""Development settings."""
from .base import *  # noqa
import os

DEBUG = True

# Use SendGrid for real email delivery
_sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
if _sendgrid_key:
    INSTALLED_APPS += ["anymail"]
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {"SENDGRID_API_KEY": _sendgrid_key}
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax CORS in dev
CORS_ALLOW_ALL_ORIGINS = True
