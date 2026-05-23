from django.contrib import admin
from .models import PitchCard, PitchLike, PitchBookmark


@admin.register(PitchCard)
class PitchCardAdmin(admin.ModelAdmin):
    list_display = ["title", "entrepreneur", "category", "stage", "funding_status", "amount_needed", "verified", "created_at"]
    list_filter = ["funding_status", "stage", "category", "verified", "verification_status"]
    search_fields = ["title", "description", "entrepreneur__email", "entrepreneur__full_name"]
    readonly_fields = ["id", "created_at", "updated_at", "likes", "views"]
    ordering = ["-created_at"]

    actions = ["mark_verified", "mark_open", "mark_funded"]

    def mark_verified(self, request, queryset):
        queryset.update(verified=True, verification_status="approved")
    mark_verified.short_description = "Mark selected pitches as verified"

    def mark_open(self, request, queryset):
        queryset.update(funding_status="open")
    mark_open.short_description = "Set funding status to Open"

    def mark_funded(self, request, queryset):
        queryset.update(funding_status="funded")
    mark_funded.short_description = "Set funding status to Funded"


@admin.register(PitchLike)
class PitchLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "pitch", "created_at"]
    search_fields = ["user__email", "pitch__title"]


@admin.register(PitchBookmark)
class PitchBookmarkAdmin(admin.ModelAdmin):
    list_display = ["user", "pitch", "created_at"]
    search_fields = ["user__email", "pitch__title"]
