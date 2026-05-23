"""Pitch views — CRUD + like/bookmark toggles."""
from django.db import models as db_models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsEntrepreneur, IsOwnerOrReadOnly
from .models import PitchCard, PitchLike, PitchBookmark
from .serializers import (
    PitchCardListSerializer,
    PitchCardDetailSerializer,
    CreatePitchSerializer,
    UpdatePitchSerializer,
)


class PitchListCreateView(APIView):
    """
    GET  /api/v1/pitches/         — list all pitches (public)
    POST /api/v1/pitches/         — create pitch (entrepreneur only)
    """
    # No explicit parser_classes — use global CamelCaseJSONParser + MultiPartParser

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsEntrepreneur()]
        return [AllowAny()]

    def get(self, request):
        queryset = PitchCard.objects.select_related("entrepreneur").prefetch_related(
            "offers", "pitch_likes", "pitch_bookmarks"
        )

        # Filter by entrepreneurId query param
        entrepreneur_id = request.query_params.get("entrepreneurId")
        if entrepreneur_id:
            queryset = queryset.filter(entrepreneur__id=entrepreneur_id)

        # Filter by category
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Filter by stage
        stage = request.query_params.get("stage")
        if stage:
            queryset = queryset.filter(stage=stage)

        # Filter by funding status
        funding_status = request.query_params.get("fundingStatus")
        if funding_status:
            queryset = queryset.filter(funding_status=funding_status)

        # Filter by location
        location = request.query_params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Search by title/description
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                db_models.Q(title__icontains=search) | db_models.Q(description__icontains=search)
            )

        # Pagination
        page_size = int(request.query_params.get("pageSize", 20))
        page = int(request.query_params.get("page", 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        pitches = queryset[start:end]

        serializer = PitchCardListSerializer(pitches, many=True, context={"request": request})
        return Response({
            "count": total,
            "page": page,
            "pageSize": page_size,
            "results": serializer.data,
        })

    def post(self, request):
        serializer = CreatePitchSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        pitch = serializer.save()
        return Response(
            PitchCardDetailSerializer(pitch, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PitchDetailView(APIView):
    """
    GET    /api/v1/pitches/:id/  — get single pitch (public)
    PUT    /api/v1/pitches/:id/  — update pitch (owner only)
    DELETE /api/v1/pitches/:id/  — delete pitch (owner only)
    """
    # No explicit parser_classes — use global CamelCaseJSONParser + MultiPartParser

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_object(self, pk):
        try:
            return PitchCard.objects.select_related("entrepreneur").prefetch_related(
                "offers__funder", "pitch_likes", "pitch_bookmarks"
            ).get(pk=pk)
        except PitchCard.DoesNotExist:
            return None

    def get(self, request, pk):
        pitch = self.get_object(pk)
        if not pitch:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        # Increment view count
        PitchCard.objects.filter(pk=pk).update(views=db_models.F("views") + 1)
        pitch.views += 1

        serializer = PitchCardDetailSerializer(pitch, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        pitch = self.get_object(pk)
        if not pitch:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, pitch)

        serializer = UpdatePitchSerializer(pitch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        pitch = serializer.save()
        return Response(PitchCardDetailSerializer(pitch, context={"request": request}).data)

    def delete(self, request, pk):
        pitch = self.get_object(pk)
        if not pitch:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, pitch)
        pitch.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)


class PitchLikeView(APIView):
    """PATCH /api/v1/pitches/:id/like/ — toggle like."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            pitch = PitchCard.objects.get(pk=pk)
        except PitchCard.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        like, created = PitchLike.objects.get_or_create(user=request.user, pitch=pitch)
        if not created:
            # Already liked — unlike it
            like.delete()
            PitchCard.objects.filter(pk=pk).update(likes=db_models.F("likes") - 1)
            pitch.likes = max(0, pitch.likes - 1)
        else:
            PitchCard.objects.filter(pk=pk).update(likes=db_models.F("likes") + 1)
            pitch.likes += 1

        # Refresh from DB
        pitch.refresh_from_db()
        return Response(PitchCardListSerializer(pitch, context={"request": request}).data)


class PitchBookmarkView(APIView):
    """PATCH /api/v1/pitches/:id/bookmark/ — toggle bookmark."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            pitch = PitchCard.objects.get(pk=pk)
        except PitchCard.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        bookmark, created = PitchBookmark.objects.get_or_create(user=request.user, pitch=pitch)
        if not created:
            bookmark.delete()

        pitch.refresh_from_db()
        return Response(PitchCardListSerializer(pitch, context={"request": request}).data)
