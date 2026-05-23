"""WeeklyProgress serializers — matches the frontend WeeklyProgressPayload interface."""
from rest_framework import serializers
from .models import WeeklyProgress


class WeeklyProgressSerializer(serializers.ModelSerializer):
    """
    Read/write serializer.
    Frontend sends: { pitchId, weekEnding, summary, wins, blockers?, nextSteps, metrics? }
    djangorestframework-camel-case handles the camelCase ↔ snake_case conversion.
    """
    pitch_id = serializers.UUIDField(write_only=True)
    pitch_title = serializers.CharField(source="pitch.title", read_only=True)

    class Meta:
        model = WeeklyProgress
        fields = [
            "id",
            "pitch_id",
            "pitch_title",
            "week_ending",
            "summary",
            "wins",
            "blockers",
            "next_steps",
            "metrics",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "pitch_title"]

    def validate_pitch_id(self, value):
        from apps.pitches.models import PitchCard
        user = self.context["request"].user
        try:
            pitch = PitchCard.objects.get(pk=value, entrepreneur=user)
        except PitchCard.DoesNotExist:
            raise serializers.ValidationError(
                "Project not found or you are not the owner."
            )
        self.pitch = pitch
        return value

    def create(self, validated_data):
        validated_data.pop("pitch_id")
        return WeeklyProgress.objects.create(
            pitch=self.pitch,
            entrepreneur=self.context["request"].user,
            **validated_data,
        )
