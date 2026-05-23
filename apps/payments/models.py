"""Payment model — tracks every Paystack transaction."""
import uuid
from django.db import models
from django.conf import settings


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    funder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
    )
    pitch = models.ForeignKey(
        "pitches.PitchCard",
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
    )
    offer = models.ForeignKey(
        "offers.FundingOffer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    # Amount in NGN (naira) — stored as decimal
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    # Amount in kobo sent to Paystack (amount * 100)
    amount_kobo = models.PositiveBigIntegerField(default=0)
    # 1.5% platform fee
    platform_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    paystack_reference = models.CharField(max_length=100, unique=True)
    paystack_transaction_id = models.CharField(max_length=100, blank=True, default="")
    paystack_authorization_url = models.URLField(blank=True, default="")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Raw Paystack webhook/verify payload for audit
    paystack_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.paystack_reference} — {self.status} — ₦{self.amount}"
