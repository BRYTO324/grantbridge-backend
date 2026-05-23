"""Payment URL patterns."""
from django.urls import path
from .views import (
    InitializePaymentView,
    VerifyPaymentView,
    PaystackWebhookView,
    PaymentHistoryView,
)

urlpatterns = [
    path("initialize/", InitializePaymentView.as_view(), name="payment-initialize"),
    path("verify/", VerifyPaymentView.as_view(), name="payment-verify"),
    path("webhook/", PaystackWebhookView.as_view(), name="payment-webhook"),
    path("history/", PaymentHistoryView.as_view(), name="payment-history"),
]
