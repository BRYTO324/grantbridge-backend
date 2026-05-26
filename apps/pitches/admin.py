from django.contrib import admin
from django.utils.html import format_html
from .models import PitchCard, PitchLike, PitchBookmark


@admin.register(PitchCard)
class PitchCardAdmin(admin.ModelAdmin):
    list_display = [
        "title", "entrepreneur", "category", "stage",
        "funding_status", "verification_status_badge",
        "amount_needed", "verified", "created_at"
    ]
    list_filter = ["funding_status", "stage", "category", "verified", "verification_status"]
    search_fields = ["title", "description", "entrepreneur__email", "entrepreneur__full_name"]
    readonly_fields = ["id", "created_at", "updated_at", "likes", "views"]
    ordering = ["-created_at"]
    list_per_page = 25

    fieldsets = (
        ("Project Info", {
            "fields": ("id", "title", "description", "category", "stage", "location", "tags")
        }),
        ("Entrepreneur", {
            "fields": ("entrepreneur",)
        }),
        ("Funding", {
            "fields": ("amount_needed", "funding_status")
        }),
        ("Verification", {
            "fields": ("verified", "verification_status")
        }),
        ("Media", {
            "fields": ("image", "media")
        }),
        ("Stats", {
            "fields": ("likes", "views", "created_at", "updated_at")
        }),
    )

    # ── Admin actions ──────────────────────────────────────────────────────────

    actions = [
        "approve_projects",
        "reject_projects",
        "mark_open",
        "mark_funded",
        "mark_closed",
        "mark_in_review",
    ]

    def approve_projects(self, request, queryset):
        """Approve selected projects — makes them visible to funders."""
        updated = queryset.update(verified=True, verification_status="approved", funding_status="open")
        # Send notification to each entrepreneur
        from apps.notifications.models import create_notification
        for pitch in queryset:
            create_notification(
                user=pitch.entrepreneur,
                notification_type="project_approved",
                title="Your project has been approved! 🎉",
                message=f'"{pitch.title}" has been approved and is now visible to funders.',
                link="/dashboard/entrepreneur/projects",
            )
        self.message_user(request, f"✅ {updated} project(s) approved and set to Open.")
    approve_projects.short_description = "✅ Approve selected projects (set to Open)"

    def reject_projects(self, request, queryset):
        """Reject selected projects."""
        updated = queryset.update(verified=False, verification_status="rejected", funding_status="closed")
        from apps.notifications.models import create_notification
        for pitch in queryset:
            create_notification(
                user=pitch.entrepreneur,
                notification_type="project_rejected",
                title="Project not approved",
                message=f'"{pitch.title}" was not approved. Please review and resubmit.',
                link="/dashboard/entrepreneur/projects",
            )
        self.message_user(request, f"❌ {updated} project(s) rejected.")
    reject_projects.short_description = "❌ Reject selected projects"

    def mark_open(self, request, queryset):
        queryset.update(funding_status="open")
        self.message_user(request, "Projects set to Open.")
    mark_open.short_description = "Set funding status → Open"

    def mark_funded(self, request, queryset):
        queryset.update(funding_status="funded")
        self.message_user(request, "Projects set to Funded.")
    mark_funded.short_description = "Set funding status → Funded"

    def mark_closed(self, request, queryset):
        queryset.update(funding_status="closed")
        self.message_user(request, "Projects set to Closed.")
    mark_closed.short_description = "Set funding status → Closed"

    def mark_in_review(self, request, queryset):
        queryset.update(funding_status="in_review", verification_status="pending")
        self.message_user(request, "Projects set to In Review.")
    mark_in_review.short_description = "Set funding status → In Review"

    # ── Display helpers ────────────────────────────────────────────────────────

    def verification_status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "approved": "#10b981",
            "rejected": "#ef4444",
        }
        color = colors.get(obj.verification_status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold">{}</span>',
            color,
            obj.verification_status.upper()
        )
    verification_status_badge.short_description = "Verification"


@admin.register(PitchLike)
class PitchLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "pitch", "created_at"]
    search_fields = ["user__email", "pitch__title"]


@admin.register(PitchBookmark)
class PitchBookmarkAdmin(admin.ModelAdmin):
    list_display = ["user", "pitch", "created_at"]
    search_fields = ["user__email", "pitch__title"]
