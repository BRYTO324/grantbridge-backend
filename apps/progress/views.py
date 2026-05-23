"""Weekly progress views."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsEntrepreneur
from .models import WeeklyProgress
from .serializers import WeeklyProgressSerializer


class WeeklyProgressView(APIView):
    """
    GET  /api/v1/progress/ — list progress updates for the authenticated entrepreneur
    POST /api/v1/progress/ — submit a new weekly update
    """
    permission_classes = [IsAuthenticated, IsEntrepreneur]

    def get(self, request):
        updates = WeeklyProgress.objects.filter(
            entrepreneur=request.user
        ).select_related("pitch")

        # Optional filter by pitch
        pitch_id = request.query_params.get("pitchId")
        if pitch_id:
            updates = updates.filter(pitch__id=pitch_id)

        serializer = WeeklyProgressSerializer(updates, many=True, context={"request": request})
        return Response({"count": updates.count(), "results": serializer.data})

    def post(self, request):
        serializer = WeeklyProgressSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        update = serializer.save()
        return Response(
            WeeklyProgressSerializer(update, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
