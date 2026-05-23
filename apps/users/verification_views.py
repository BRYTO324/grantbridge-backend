"""Verification document views."""
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import VerificationDocumentSerializer, UserSerializer


class SubmitVerificationView(APIView):
    """POST /api/v1/verification/submit/ — upload KYC documents."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = VerificationDocumentSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = UserSerializer(request.user, context={"request": request}).data
        return Response(
            {
                "message": "Verification documents submitted. We'll review them shortly.",
                "verificationStatus": "submitted",
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerificationStatusView(APIView):
    """GET /api/v1/verification/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        doc = getattr(user, "verification_document", None)
        return Response(
            {
                "verificationStatus": user.verification_status,
                "submittedAt": doc.submitted_at.isoformat() if doc else None,
            }
        )
