from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VerificationDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "role", "verification_status", "email_verified", "date_joined"]
    list_filter = ["role", "verification_status", "email_verified", "is_staff"]
    search_fields = ["email", "full_name", "company"]
    ordering = ["-date_joined"]
    readonly_fields = ["id", "date_joined"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role", "company", "phone", "avatar")}),
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


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ["user", "id_type", "submitted_at"]
    list_filter = ["id_type"]
    search_fields = ["user__email", "id_number"]
    readonly_fields = ["submitted_at"]
