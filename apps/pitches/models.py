"""PitchCard, PitchLike, and PitchBookmark models."""
import uuid
from django.db import models
from django.conf import settings


class PitchCard(models.Model):
    FUNDING_STATUS_CHOICES = [
        ("open", "Open"),
        ("funded", "Funded"),
        ("in_review", "In Review"),
        ("closed", "Closed"),
    ]
    STAGE_CHOICES = [
        ("idea", "Idea"),
        ("mvp", "MVP"),
        ("growth", "Growth"),
        ("scale", "Scale"),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrepreneur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pitches",
        limit_choices_to={"role": "entrepreneur"},
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    amount_needed = models.DecimalField(max_digits=15, decimal_places=2)
    funding_status = models.CharField(
        max_length=20,
        choices=FUNDING_STATUS_CHOICES,
        default="open",
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="idea")
    location = models.CharField(max_length=255, blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to="pitches/images/", blank=True, null=True)
    media = models.JSONField(default=list, blank=True)  # List of image URLs
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pitches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} by {self.entrepreneur.full_name}"

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return ""


class PitchLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="liked_pitches",
    )
    pitch = models.ForeignKey(
        PitchCard,
        on_delete=models.CASCADE,
        related_name="pitch_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pitch_likes"
        unique_together = [("user", "pitch")]

    def __str__(self):
        return f"{self.user.email} liked {self.pitch.title}"


class PitchBookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarked_pitches",
    )
    pitch = models.ForeignKey(
        PitchCard,
        on_delete=models.CASCADE,
        related_name="pitch_bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pitch_bookmarks"
        unique_together = [("user", "pitch")]

    def __str__(self):
        return f"{self.user.email} bookmarked {self.pitch.title}"
