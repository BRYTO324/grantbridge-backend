"""Offer URL patterns."""
from django.urls import path
from .views import SubmitOfferView, UpdateOfferView

urlpatterns = [
    path("", SubmitOfferView.as_view(), name="offer-submit"),
    path("<uuid:pk>/", UpdateOfferView.as_view(), name="offer-update"),
]
