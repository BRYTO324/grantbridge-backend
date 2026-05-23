"""Serializers for User auth and profile."""
import secrets
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, VerificationDocument


class UserSerializer(serializers.ModelSerializer):
    """Public user representation — matches the frontend User interface."""
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "role", "company", "phone",
            "avatar_url", "verification_status", "profile_completed",
            "email_verified", "date_joined", "location", "website", "bio",
        ]
        read_only_fields = ["id", "email", "role", "date_joined", "email_verified"]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return ""


class RegisterSerializer(serializers.ModelSerializer):
    """Register a new user (entrepreneur or funder)."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    # password_confirm is optional — the frontend validates match client-side
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "full_name", "role", "company", "phone"]

    def validate(self, attrs):
        confirm = attrs.get("password_confirm")
        if confirm and attrs["password"] != confirm:
            raise serializers.ValidationError({"error": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")

        # Generate email verification token
        token = secrets.token_urlsafe(32)
        user = User(**validated_data)
        user.set_password(password)
        user.email_verification_token = token
        user.is_active = True  # Active but email_verified=False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Login with email + password + role."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["entrepreneur", "funder"])

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]
        role = attrs["role"]

        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if not user:
            raise serializers.ValidationError({"error": "Invalid email or password."})

        if user.role != role:
            raise serializers.ValidationError(
                {"error": f"This account is registered as a {user.role}, not a {role}."}
            )

        if not user.is_active:
            raise serializers.ValidationError({"error": "This account has been deactivated."})

        attrs["user"] = user
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """PATCH /auth/me/ — update profile fields."""
    # CharField so any string is accepted — frontend validates URL format
    website = serializers.CharField(max_length=500, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = [
            "full_name", "company", "phone", "avatar",
            "profile_completed", "location", "website", "bio",
        ]

    def update(self, instance, validated_data):
        # If no data provided, just return the current instance (used for refresh)
        if not validated_data:
            return instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value.lower().strip())
        except User.DoesNotExist:
            # Don't reveal whether the email exists
            self.user = None
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate(self, attrs):
        token = attrs["token"]
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Invalid or expired reset token."})

        # Token expires after 1 hour
        if user.password_reset_token_created_at:
            elapsed = timezone.now() - user.password_reset_token_created_at
            if elapsed.total_seconds() > 3600:
                raise serializers.ValidationError({"error": "Reset token has expired."})

        attrs["user"] = user
        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            self.user = User.objects.get(email_verification_token=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification link.")
        return value


class VerificationDocumentSerializer(serializers.ModelSerializer):
    """Submit KYC documents."""
    # Accept any id_type string — don't restrict to model choices
    id_type = serializers.CharField(max_length=30)
    id_back = serializers.FileField(required=False, allow_null=True)
    selfie = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = VerificationDocument
        fields = ["id_type", "id_number", "id_front", "id_back", "selfie", "submitted_at"]
        read_only_fields = ["submitted_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        # Remove null optional files
        validated_data.pop("selfie", None) if not validated_data.get("selfie") else None
        validated_data.pop("id_back", None) if not validated_data.get("id_back") else None

        doc, _ = VerificationDocument.objects.update_or_create(
            user=user,
            defaults=validated_data,
        )
        # Update user verification status
        user.verification_status = "submitted"
        user.save(update_fields=["verification_status"])
        return doc
