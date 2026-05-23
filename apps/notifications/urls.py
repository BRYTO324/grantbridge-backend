from django.urls import path
from .views import NotificationListView, MarkAllReadView, MarkOneReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("read-all/", MarkAllReadView.as_view(), name="notification-read-all"),
    path("<uuid:pk>/read/", MarkOneReadView.as_view(), name="notification-read-one"),
]
