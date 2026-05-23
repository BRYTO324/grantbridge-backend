"""Progress URL patterns."""
from django.urls import path
from .views import WeeklyProgressView

urlpatterns = [
    path("", WeeklyProgressView.as_view(), name="progress-list-create"),
]
