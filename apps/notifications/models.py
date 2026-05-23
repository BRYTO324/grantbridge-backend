"""Notification model — stores in-app notifications for users."""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        # Entrepreneur notifications
        ("project_approved", "Project Approved"),
        ("project_rejected", "Project Rejected"),
        ("offer_received", "Funding Offer Received"),
        ("offer_accepted", "Offer Accepted"),
        ("offer_rejected", "Offer Rejected"),
        # Funder notifications
        ("offer_accepted_funder", "Your Offer Was Accepted"),
        ("offer_rejected_funder", "Your Offer Was Rejected"),
        ("project_funded", "Project Funded"),
        # General
        ("verification_approved", "Account Verified"),
        ("verification_rejected", "Verification Rejected"),
        ("payment_success", "Payment Successful"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    # Optional link to related object
    link = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.notification_type} — {'read' if self.is_read else 'unread'}"


def create_notification(user, notification_type: str, title: str, message: str, link: str = ""):
    """Helper to create a notification for a user."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
