"""WeeklyProgress model."""
import uuid
from django.db import models
from django.conf import settings


class WeeklyProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pitch = models.ForeignKey(
        "pitches.PitchCard",
        on_delete=models.CASCADE,
        related_name="progress_updates",
    )
    entrepreneur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_updates",
        limit_choices_to={"role": "entrepreneur"},
    )
    week_ending = models.DateField()
    summary = models.TextField()
    wins = models.TextField()
    blockers = models.TextField(blank=True, default="")
    next_steps = models.TextField()
    metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weekly_progress"
        ordering = ["-week_ending"]
        # One update per pitch per week
        unique_together = [("pitch", "week_ending")]

    def __str__(self):
        return f"Progress for {self.pitch.title} — week ending {self.week_ending}"
