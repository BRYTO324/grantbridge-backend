"""Payment serializers."""
from decimal import Decimal
from rest_framework import serializers
from .models import Payment
from .paystack import calculate_fee


class InitializePaymentSerializer(serializers.Serializer):
    """POST /api/v1/payments/initialize/"""
    pitch_id = serializers.UUIDField()
    offer_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    def validate_pitch_id(self, value):
        from apps.pitches.models import PitchCard
        try:
            self.pitch = PitchCard.objects.get(pk=value)
        except PitchCard.DoesNotExist:
            raise serializers.ValidationError("Project not found.")
        if self.pitch.funding_status not in ("open", "in_review"):
            raise serializers.ValidationError("This project is not accepting payments.")
        return value

    def validate_offer_id(self, value):
        if value is None:
            self.offer = None
            return value
        from apps.offers.models import FundingOffer
        try:
            self.offer = FundingOffer.objects.get(pk=value)
        except FundingOffer.DoesNotExist:
            raise serializers.ValidationError("Offer not found.")
        return value

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """POST /api/v1/payments/verify/"""
    reference = serializers.CharField(max_length=100)


class PaymentSerializer(serializers.ModelSerializer):
    """Read serializer for payment history."""
    pitch_title = serializers.CharField(source="pitch.title", default="")
    funder_name = serializers.CharField(source="funder.full_name", default="")

    class Meta:
        model = Payment
        fields = [
            "id",
            "funder_name",
            "pitch_title",
            "amount",
            "platform_fee",
            "paystack_reference",
            "status",
            "paid_at",
            "created_at",
        ]
