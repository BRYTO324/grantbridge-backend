"""Pitch URL patterns."""
from django.urls import path
from .views import (
    PitchListCreateView,
    PitchDetailView,
    PitchLikeView,
    PitchBookmarkView,
)
from .upload_views import MediaUploadView

urlpatterns = [
    path("", PitchListCreateView.as_view(), name="pitch-list-create"),
    path("upload-media/", MediaUploadView.as_view(), name="pitch-upload-media"),
    path("<uuid:pk>/", PitchDetailView.as_view(), name="pitch-detail"),
    path("<uuid:pk>/like/", PitchLikeView.as_view(), name="pitch-like"),
    path("<uuid:pk>/bookmark/", PitchBookmarkView.as_view(), name="pitch-bookmark"),
]
