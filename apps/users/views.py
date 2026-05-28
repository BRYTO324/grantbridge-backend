"""Auth and user profile views."""
import secrets
import logging
import threading
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
)

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _send_email_async(subject, message, from_email, recipient_list):
    """Send email in a background thread — never blocks the HTTP response."""
    def _worker():
        try:
            from django.core.mail import send_mail as _send_mail
            _send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email sent: '{subject}' to {recipient_list}")
        except Exception as e:
            logger.error(f"Email failed: '{subject}' to {recipient_list} — {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def send_verification_email(user, request=None):
    """Send email verification link — non-blocking background thread."""
    token = user.email_verification_token
    frontend_url = settings.FRONTEND_URL
    verify_url = f"{frontend_url}/verify-email/{user.role}?token={token}"

    _send_email_async(
        subject="Welcome to GrantBridge — Verify Your Email",
        message=(
            f"Hi {user.full_name},\n\n"
            f"Welcome to GrantBridge!\n\n"
            f"Please verify your email by clicking the link below:\n\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you didn't create this account, ignore this email.\n\n"
            f"— The GrantBridge Team\n"
            f"https://grantbridge-frontend.vercel.app"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    logger.info(f"Verification email queued for {user.email}")


def send_password_reset_email(user):
    """Send password reset link — non-blocking background thread."""
    token = user.password_reset_token
    frontend_url = settings.FRONTEND_URL
    reset_url = f"{frontend_url}/reset-password/{user.role}?token={token}"

    _send_email_async(
        subject="Reset Your GrantBridge Password",
        message=(
            f"Hi {user.full_name},\n\n"
            f"Click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour.\n\n"
            f"If you didn't request this, ignore this email.\n\n"
            f"— The GrantBridge Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    logger.info(f"Password reset email queued for {user.email}")


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto-verify so users can use the app immediately
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        # Send welcome/verification email in background (non-blocking)
        send_verification_email(user, request)

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user, context={"request": request}).data

        return Response(
            {
                "user": user_data,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "message": "Account created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user, context={"request": request}).data

        return Response({
            "user": user_data,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        })


class LogoutView(APIView):
    """POST /api/v1/auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully."})


class TokenRefreshView(APIView):
    """POST /api/v1/auth/token/refresh/"""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            return Response({"access": str(token.access_token)})
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyEmailView(APIView):
    """POST /api/v1/auth/verify-email/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.email_verified = True
        user.email_verification_token = ""
        user.save(update_fields=["email_verified", "email_verification_token"])
        return Response({"message": "Email verified successfully."})


class ResendVerificationView(APIView):
    """POST /api/v1/auth/resend-verification/"""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "If that email exists, a verification link has been sent."})

        if user.email_verified:
            return Response({"message": "Email is already verified."})

        user.email_verification_token = secrets.token_urlsafe(32)
        user.save(update_fields=["email_verification_token"])
        send_verification_email(user, request)
        return Response({"message": "If that email exists, a verification link has been sent."})


class ForgotPasswordView(APIView):
    """POST /api/v1/auth/forgot-password/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = getattr(serializer, "user", None)

        if user:
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_token_created_at = timezone.now()
            user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])
            send_password_reset_email(user)

        return Response({"message": "If that email exists, a password reset link has been sent."})


class ResetPasswordView(APIView):
    """POST /api/v1/auth/reset-password/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.password_reset_token = ""
        user.password_reset_token_created_at = None
        user.save(update_fields=["password", "password_reset_token", "password_reset_token_created_at"])
        return Response({"message": "Password reset successfully."})


class MeView(APIView):
    """GET/PATCH /api/v1/auth/me/"""
    permission_classes = [IsAuthenticated]
    # NO explicit parser_classes — uses global CamelCaseJSONParser + MultiPartParser

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")

        if not current_password or not new_password:
            return Response(
                {"error": "Current password and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"message": "Password changed successfully."})
