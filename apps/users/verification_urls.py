"""Verification URL patterns."""
from django.urls import path
from .verification_views import SubmitVerificationView, VerificationStatusView

urlpatterns = [
    path("submit/", SubmitVerificationView.as_view(), name="verification-submit"),
    path("status/", VerificationStatusView.as_view(), name="verification-status"),
]
