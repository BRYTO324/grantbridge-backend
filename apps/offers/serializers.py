"""FundingOffer serializers — output matches the frontend FundingOffer interface."""
from rest_framework import serializers
from .models import FundingOffer


class FundingOfferSerializer(serializers.ModelSerializer):
    """
    Read serializer — nested inside PitchCardDetailSerializer.
    Matches the frontend FundingOffer TypeScript interface.
    """
    funder_id = serializers.CharField(source="funder.id")
    funder_name = serializers.CharField(source="funder.full_name")
    funder_company = serializers.CharField(source="funder.company")

    class Meta:
        model = FundingOffer
        fields = [
            "id",
            "funder_id",
            "funder_name",
            "funder_company",
            "amount",
            "message",
            "status",
            "created_at",
        ]


class SubmitOfferSerializer(serializers.ModelSerializer):
    """
    POST /api/v1/offers/ — funder submits an offer on a pitch.
    Frontend sends: { pitchId, amount, message, funderName, funderCompany }
    """
    pitch_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = FundingOffer
        fields = ["pitch_id", "amount", "message"]

    def validate_pitch_id(self, value):
        from apps.pitches.models import PitchCard
        try:
            pitch = PitchCard.objects.get(pk=value)
        except PitchCard.DoesNotExist:
            raise serializers.ValidationError("Project not found.")

        if pitch.funding_status != "open":
            raise serializers.ValidationError("This project is not open for funding.")

        self.pitch = pitch
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        # Prevent duplicate pending offers from the same funder
        if FundingOffer.objects.filter(
            pitch=self.pitch, funder=user, status="pending"
        ).exists():
            raise serializers.ValidationError(
                {"error": "You already have a pending offer on this project."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("pitch_id")
        offer = FundingOffer.objects.create(
            pitch=self.pitch,
            funder=self.context["request"].user,
            **validated_data,
        )
        # Notify the entrepreneur they received a new offer
        from apps.notifications.models import create_notification
        funder = self.context["request"].user
        create_notification(
            user=self.pitch.entrepreneur,
            notification_type="offer_received",
            title="New funding offer received! 💰",
            message=f'{funder.full_name} ({funder.company or "Independent Funder"}) has made an offer of ₦{offer.amount:,.0f} on "{self.pitch.title}".',
            link=f"/dashboard/entrepreneur/projects",
        )
        return offer


class UpdateOfferStatusSerializer(serializers.ModelSerializer):
    """
    PUT /api/v1/offers/:id/ — entrepreneur accepts or rejects an offer.
    Frontend sends: { pitchId, status: "accepted" | "rejected" }
    """
    pitch_id = serializers.UUIDField(write_only=True)
    status = serializers.ChoiceField(choices=["accepted", "rejected"])

    class Meta:
        model = FundingOffer
        fields = ["pitch_id", "status"]

    def validate_pitch_id(self, value):
        from apps.pitches.models import PitchCard
        try:
            self.pitch = PitchCard.objects.get(pk=value)
        except PitchCard.DoesNotExist:
            raise serializers.ValidationError("Project not found.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        # Only the pitch owner can accept/reject
        if self.pitch.entrepreneur != request.user:
            raise serializers.ValidationError(
                {"error": "Only the project owner can accept or reject offers."}
            )
        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data["status"]
        instance.status = new_status
        instance.save(update_fields=["status", "updated_at"])

        # If accepted, mark pitch as funded and reject all other pending offers
        if new_status == "accepted":
            pitch = instance.pitch
            pitch.funding_status = "funded"
            pitch.save(update_fields=["funding_status"])

            # Reject all other pending offers on this pitch
            FundingOffer.objects.filter(
                pitch=pitch, status="pending"
            ).exclude(pk=instance.pk).update(status="rejected")

            # Notify the funder their offer was accepted
            from apps.notifications.models import create_notification
            create_notification(
                user=instance.funder,
                notification_type="offer_accepted_funder",
                title="Your funding offer was accepted! 🎉",
                message=f'Your offer of ₦{instance.amount:,.0f} for "{pitch.title}" has been accepted by the entrepreneur.',
                link=f"/dashboard/funder/project/{pitch.id}",
            )
            # Notify the entrepreneur their project is funded
            create_notification(
                user=pitch.entrepreneur,
                notification_type="project_funded",
                title="Your project has been funded! 🎉",
                message=f'"{pitch.title}" has been funded by {instance.funder.full_name} ({instance.funder.company or "Independent Funder"}).',
                link=f"/dashboard/entrepreneur/projects",
            )
        elif new_status == "rejected":
            # Notify the funder their offer was rejected
            from apps.notifications.models import create_notification
            create_notification(
                user=instance.funder,
                notification_type="offer_rejected_funder",
                title="Funding offer not accepted",
                message=f'Your offer for "{instance.pitch.title}" was not accepted by the entrepreneur.',
                link=f"/dashboard/funder/discover",
            )

        return instance
