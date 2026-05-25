"""Auth and user profile views."""
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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


def get_tokens_for_user(user):
    """Generate JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def send_verification_email(user, request=None):
    """Send email verification link — completely non-blocking."""
    import threading

    def _send():
        try:
            from django.core.mail import send_mail as _send_mail
            token = user.email_verification_token
            frontend_url = settings.FRONTEND_URL
            verify_url = f"{frontend_url}/verify-email/{user.role}?token={token}"
            _send_mail(
                subject="Verify your GrantBridge email",
                message=(
                    f"Hi {user.full_name},\n\n"
                    f"Verify your email:\n{verify_url}\n\n"
                    f"Link expires in 24 hours.\n\n— GrantBridge Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Never block registration

    t = threading.Thread(target=_send, daemon=True)
    t.start()
    # Return immediately — don't wait for email


def send_password_reset_email(user):
    """Send password reset link — completely non-blocking."""
    import threading

    def _send():
        try:
            from django.core.mail import send_mail as _send_mail
            token = user.password_reset_token
            frontend_url = settings.FRONTEND_URL
            reset_url = f"{frontend_url}/reset-password/{user.role}?token={token}"
            _send_mail(
                subject="Reset your GrantBridge password",
                message=(
                    f"Hi {user.full_name},\n\n"
                    f"Reset your password:\n{reset_url}\n\n"
                    f"Link expires in 1 hour.\n\n— GrantBridge Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    t = threading.Thread(target=_send, daemon=True)
    t.start()


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_verification_email(user, request)
        except Exception:
            pass  # Don't fail registration if email fails — user can resend

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user, context={"request": request}).data

        return Response(
            {
                "user": user_data,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "message": "Account created. Please verify your email.",
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

        return Response(
            {
                "user": user_data,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            }
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist the refresh token."""
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
            # Don't reveal whether email exists
            return Response({"message": "If that email exists, a verification link has been sent."})

        if user.email_verified:
            return Response({"message": "Email is already verified."})

        # Regenerate token
        user.email_verification_token = secrets.token_urlsafe(32)
        user.save(update_fields=["email_verification_token"])

        try:
            send_verification_email(user, request)
        except Exception:
            pass

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
            try:
                send_password_reset_email(user)
            except Exception:
                pass

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
    # No explicit parser_classes — use global CamelCaseJSONParser + MultiPartParser

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
        # CamelCaseJSONParser converts currentPassword → current_password
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
