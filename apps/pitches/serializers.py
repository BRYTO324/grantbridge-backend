"""
Pitch serializers — output matches the frontend PitchCard TypeScript interface.
Field names are snake_case here; djangorestframework-camel-case converts them
to camelCase automatically in the response.
"""
from rest_framework import serializers
from .models import PitchCard, PitchLike, PitchBookmark


class FundedBySerializer(serializers.Serializer):
    """Nested funded_by block inside PitchCard."""
    funder_id = serializers.CharField()
    funder_name = serializers.CharField()
    funder_company = serializers.CharField()
    funded_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    funded_date = serializers.CharField()


class PitchCardListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.
    Includes liked_by_me and bookmarked_by_me for the authenticated user.
    """
    entrepreneur_id = serializers.CharField(source="entrepreneur.id")
    entrepreneur_name = serializers.CharField(source="entrepreneur.full_name")
    entrepreneur_avatar = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="entrepreneur.company")
    image_url = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    bookmarked_by_me = serializers.SerializerMethodField()
    amount_needed = serializers.DecimalField(max_digits=15, decimal_places=2)
    funded_by = serializers.SerializerMethodField()

    class Meta:
        model = PitchCard
        fields = [
            "id",
            "title",
            "description",
            "category",
            "amount_needed",
            "funding_status",
            "funded_by",
            "entrepreneur_id",
            "entrepreneur_name",
            "entrepreneur_avatar",
            "company_name",
            "location",
            "created_at",
            "tags",
            "stage",
            "likes",
            "views",
            "image_url",
            "media",
            "verified",
            "verification_status",
            "liked_by_me",
            "bookmarked_by_me",
        ]

    def get_entrepreneur_avatar(self, obj):
        request = self.context.get("request")
        if obj.entrepreneur.avatar and request:
            return request.build_absolute_uri(obj.entrepreneur.avatar.url)
        return ""

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return ""

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PitchLike.objects.filter(user=request.user, pitch=obj).exists()
        return False

    def get_bookmarked_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PitchBookmark.objects.filter(user=request.user, pitch=obj).exists()
        return False

    def get_funded_by(self, obj):
        """Return funded_by info from the accepted offer if pitch is funded."""
        if obj.funding_status == "funded":
            accepted = obj.offers.filter(status="accepted").select_related("funder").first()
            if accepted:
                return {
                    "funder_id": str(accepted.funder.id),
                    "funder_name": accepted.funder.full_name,
                    "funder_company": accepted.funder.company,
                    "funded_amount": str(accepted.amount),
                    "funded_date": accepted.updated_at.isoformat() if hasattr(accepted, "updated_at") else "",
                }
        return None


class PitchCardDetailSerializer(PitchCardListSerializer):
    """
    Full pitch detail — includes nested offers.
    Imported here to avoid circular imports; offers app serializer is inlined.
    """
    offers = serializers.SerializerMethodField()

    class Meta(PitchCardListSerializer.Meta):
        fields = PitchCardListSerializer.Meta.fields + ["offers"]

    def get_offers(self, obj):
        from apps.offers.serializers import FundingOfferSerializer
        offers = obj.offers.all().select_related("funder")
        return FundingOfferSerializer(offers, many=True, context=self.context).data


class CreatePitchSerializer(serializers.ModelSerializer):
    """POST /pitches/ — create a new pitch."""

    class Meta:
        model = PitchCard
        fields = [
            "title",
            "description",
            "category",
            "amount_needed",
            "stage",
            "location",
            "tags",
            "image",
            "media",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return PitchCard.objects.create(entrepreneur=user, **validated_data)


class UpdatePitchSerializer(serializers.ModelSerializer):
    """PUT /pitches/:id/ — update a pitch."""

    class Meta:
        model = PitchCard
        fields = [
            "title",
            "description",
            "category",
            "amount_needed",
            "stage",
            "location",
            "tags",
            "image",
            "media",
            "funding_status",
        ]
