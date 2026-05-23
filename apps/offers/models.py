"""FundingOffer model."""
import uuid
from django.db import models
from django.conf import settings


class FundingOffer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pitch = models.ForeignKey(
        "pitches.PitchCard",
        on_delete=models.CASCADE,
        related_name="offers",
    )
    funder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="funding_offers",
        limit_choices_to={"role": "funder"},
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    message = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "funding_offers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Offer by {self.funder.full_name} on {self.pitch.title} — {self.status}"
