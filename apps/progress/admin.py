from django.contrib import admin
from .models import WeeklyProgress


@admin.register(WeeklyProgress)
class WeeklyProgressAdmin(admin.ModelAdmin):
    list_display = ["pitch", "entrepreneur", "week_ending", "created_at"]
    list_filter = ["week_ending"]
    search_fields = ["pitch__title", "entrepreneur__email", "summary"]
    readonly_fields = ["id", "created_at"]
    ordering = ["-week_ending"]
