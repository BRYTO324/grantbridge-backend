"""Funding offer views."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsFunder
from apps.pitches.models import PitchCard
from apps.pitches.serializers import PitchCardDetailSerializer
from .models import FundingOffer
from .serializers import SubmitOfferSerializer, UpdateOfferStatusSerializer


class SubmitOfferView(APIView):
    """POST /api/v1/offers/ — funder submits a funding offer."""
    permission_classes = [IsAuthenticated, IsFunder]

    def post(self, request):
        serializer = SubmitOfferSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()

        # Return the full updated pitch (matches frontend expectation)
        pitch = offer.pitch
        pitch_data = PitchCardDetailSerializer(pitch, context={"request": request}).data
        return Response(pitch_data, status=status.HTTP_201_CREATED)


class UpdateOfferView(APIView):
    """PUT /api/v1/offers/:id/ — entrepreneur accepts or rejects an offer."""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            offer = FundingOffer.objects.select_related("pitch__entrepreneur", "funder").get(pk=pk)
        except FundingOffer.DoesNotExist:
            return Response({"error": "Offer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only the pitch owner can update offer status
        if offer.pitch.entrepreneur != request.user:
            return Response(
                {"error": "Only the project owner can accept or reject offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateOfferStatusSerializer(
            offer,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return the full updated pitch
        pitch = offer.pitch
        pitch.refresh_from_db()
        pitch_data = PitchCardDetailSerializer(pitch, context={"request": request}).data
        return Response(pitch_data)
