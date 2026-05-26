from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, VerificationDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "full_name", "role", "verification_badge",
        "email_verified", "profile_completed", "is_staff", "date_joined"
    ]
    list_filter = ["role", "verification_status", "email_verified", "is_staff", "profile_completed"]
    search_fields = ["email", "full_name", "company"]
    ordering = ["-date_joined"]
    readonly_fields = ["id", "date_joined"]
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role", "company", "phone", "avatar", "location", "website", "bio")}),
        ("Verification", {"fields": ("verification_status", "email_verified", "profile_completed")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )

    actions = ["verify_users", "reject_verification", "activate_users", "deactivate_users"]

    def verify_users(self, request, queryset):
        updated = queryset.update(verification_status="verified", email_verified=True)
        from apps.notifications.models import create_notification
        for user in queryset:
            create_notification(
                user=user,
                notification_type="verification_approved",
                title="Account Verified! 🎉",
                message="Your identity has been verified. You now have full access to GrantBridge.",
                link="/dashboard",
            )
        self.message_user(request, f"✅ {updated} user(s) verified.")
    verify_users.short_description = "✅ Verify selected users (approve KYC)"

    def reject_verification(self, request, queryset):
        updated = queryset.update(verification_status="rejected")
        from apps.notifications.models import create_notification
        for user in queryset:
            create_notification(
                user=user,
                notification_type="verification_rejected",
                title="Verification Not Approved",
                message="Your identity verification was not approved. Please resubmit with clearer documents.",
                link="/dashboard/entrepreneur/profile",
            )
        self.message_user(request, f"❌ {updated} user(s) verification rejected.")
    reject_verification.short_description = "❌ Reject KYC verification"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Users activated.")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Users deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

    def verification_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "submitted": "#3b82f6",
            "verified": "#10b981",
            "rejected": "#ef4444",
        }
        color = colors.get(obj.verification_status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold">{}</span>',
            color,
            obj.verification_status.upper()
        )
    verification_badge.short_description = "KYC Status"


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ["user", "id_type", "id_number", "submitted_at", "view_documents"]
    list_filter = ["id_type"]
    search_fields = ["user__email", "user__full_name", "id_number"]
    readonly_fields = ["submitted_at", "id_front_preview", "id_back_preview", "selfie_preview"]

    def view_documents(self, obj):
        links = []
        if obj.id_front:
            links.append(f'<a href="{obj.id_front.url}" target="_blank">Front</a>')
        if obj.id_back:
            links.append(f'<a href="{obj.id_back.url}" target="_blank">Back</a>')
        if obj.selfie:
            links.append(f'<a href="{obj.selfie.url}" target="_blank">Selfie</a>')
        return format_html(" | ".join(links)) if links else "No files"
    view_documents.short_description = "Documents"

    def id_front_preview(self, obj):
        if obj.id_front:
            return format_html('<img src="{}" style="max-width:300px;max-height:200px" />', obj.id_front.url)
        return "No file"
    id_front_preview.short_description = "ID Front Preview"

    def id_back_preview(self, obj):
        if obj.id_back:
            return format_html('<img src="{}" style="max-width:300px;max-height:200px" />', obj.id_back.url)
        return "No file"
    id_back_preview.short_description = "ID Back Preview"

    def selfie_preview(self, obj):
        if obj.selfie:
            return format_html('<img src="{}" style="max-width:300px;max-height:200px" />', obj.selfie.url)
        return "No file"
    selfie_preview.short_description = "Selfie Preview"
