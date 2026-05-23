"""Media upload endpoint — accepts images/videos and returns their served URLs."""
import os
import uuid
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB


class MediaUploadView(APIView):
    """
    POST /api/v1/pitches/upload-media/
    Accepts a single file (image or video), saves it, returns the URL.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        content_type = file.content_type
        is_video = content_type in ALLOWED_VIDEO_TYPES
        is_image = content_type in ALLOWED_IMAGE_TYPES

        if not is_image and not is_video:
            return Response(
                {"error": f"Unsupported file type: {content_type}. Use JPEG, PNG, WebP, MP4, or WebM."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = MAX_VIDEO_SIZE if is_video else MAX_IMAGE_SIZE
        if file.size > max_size:
            limit_mb = max_size // (1024 * 1024)
            return Response(
                {"error": f"File too large. Maximum size is {limit_mb}MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build a safe filename
        ext = os.path.splitext(file.name)[1].lower() or (".mp4" if is_video else ".jpg")
        filename = f"{uuid.uuid4().hex}{ext}"
        subfolder = "pitches/videos/" if is_video else "pitches/media/"
        relative_path = os.path.join(subfolder, filename)
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        with open(full_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Build absolute URL
        url = request.build_absolute_uri(settings.MEDIA_URL + relative_path.replace("\\", "/"))

        return Response(
            {
                "url": url,
                "filename": filename,
                "contentType": content_type,
                "isVideo": is_video,
                "size": file.size,
            },
            status=status.HTTP_201_CREATED,
        )
