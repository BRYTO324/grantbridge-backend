"""
Payment views — Paystack integration.

Flow:
  1. POST /payments/initialize/  → create pending Payment, get Paystack authorization_url
  2. User pays on Paystack hosted page
  3. POST /payments/verify/      → verify with Paystack, mark payment success/failed
  4. POST /payments/webhook/     → Paystack server-to-server confirmation (backup)
"""
import json
import logging

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsFunder
from apps.pitches.models import PitchCard
from .models import Payment
from .serializers import InitializePaymentSerializer, VerifyPaymentSerializer, PaymentSerializer
from .paystack import (
    generate_reference,
    calculate_fee,
    initialize_transaction,
    verify_transaction,
    validate_webhook_signature,
)

logger = logging.getLogger(__name__)


class InitializePaymentView(APIView):
    """POST /api/v1/payments/initialize/"""
    permission_classes = [IsAuthenticated, IsFunder]

    def post(self, request):
        serializer = InitializePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pitch = serializer.pitch
        offer = getattr(serializer, "offer", None)
        base_amount = serializer.validated_data["amount"]

        # Calculate fee breakdown
        fee_data = calculate_fee(base_amount)
        reference = generate_reference()

        # Create a pending Payment record before calling Paystack
        payment = Payment.objects.create(
            funder=request.user,
            pitch=pitch,
            offer=offer,
            amount=fee_data["base_amount"],
            amount_kobo=fee_data["total_kobo"],
            platform_fee=fee_data["platform_fee"],
            paystack_reference=reference,
            status="pending",
        )

        # Call Paystack
        try:
            paystack_data = initialize_transaction(
                email=request.user.email,
                amount_kobo=fee_data["total_kobo"],
                reference=reference,
                metadata={
                    "pitch_id": str(pitch.id),
                    "pitch_title": pitch.title,
                    "funder_id": str(request.user.id),
                    "funder_name": request.user.full_name,
                    "offer_id": str(offer.id) if offer else None,
                    "payment_id": str(payment.id),
                },
            )
        except ValueError as e:
            payment.status = "failed"
            payment.save(update_fields=["status"])
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Save the authorization URL
        payment.paystack_authorization_url = paystack_data.get("authorization_url", "")
        payment.save(update_fields=["paystack_authorization_url"])

        return Response(
            {
                "reference": reference,
                "authorizationUrl": paystack_data.get("authorization_url"),
                "accessCode": paystack_data.get("access_code"),
                "amount": str(fee_data["base_amount"]),
                "platformFee": str(fee_data["platform_fee"]),
                "totalAmount": str(fee_data["total_amount"]),
                "paystackPublicKey": __import__("django.conf", fromlist=["settings"]).settings.PAYSTACK_PUBLIC_KEY,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyPaymentView(APIView):
    """POST /api/v1/payments/verify/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data["reference"]

        # Find the payment record
        try:
            payment = Payment.objects.select_related("pitch", "offer", "funder").get(
                paystack_reference=reference
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found."}, status=status.HTTP_404_NOT_FOUND)

        # Don't re-verify already successful payments
        if payment.status == "success":
            return Response(
                {
                    "status": "success",
                    "message": "Payment already verified.",
                    "reference": reference,
                    "amount": str(payment.amount),
                    "paidAt": payment.paid_at.isoformat() if payment.paid_at else None,
                }
            )

        # Call Paystack verify
        try:
            tx_data = verify_transaction(reference)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Save raw payload for audit
        payment.paystack_payload = tx_data
        payment.paystack_transaction_id = str(tx_data.get("id", ""))

        if tx_data.get("status") == "success":
            payment.status = "success"
            payment.paid_at = timezone.now()
            payment.save(update_fields=[
                "status", "paid_at", "paystack_transaction_id", "paystack_payload"
            ])
            _handle_successful_payment(payment)

            return Response(
                {
                    "status": "success",
                    "message": "Payment verified successfully.",
                    "reference": reference,
                    "amount": str(payment.amount),
                    "paidAt": payment.paid_at.isoformat(),
                    "transactionId": payment.paystack_transaction_id,
                }
            )
        else:
            payment.status = "failed"
            payment.save(update_fields=["status", "paystack_transaction_id", "paystack_payload"])
            return Response(
                {"error": "Payment was not successful.", "paystackStatus": tx_data.get("status")},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    """
    POST /api/v1/payments/webhook/
    Paystack server-to-server webhook — backup confirmation.
    Must be exempt from CSRF and authentication.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No JWT auth for webhooks

    def post(self, request):
        # Validate signature
        signature = request.headers.get("X-Paystack-Signature", "")
        if not validate_webhook_signature(request.body, signature):
            logger.warning("Invalid Paystack webhook signature received.")
            return Response({"error": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)

        event = payload.get("event")
        data = payload.get("data", {})

        if event == "charge.success":
            reference = data.get("reference")
            if reference:
                try:
                    payment = Payment.objects.select_related("pitch", "offer").get(
                        paystack_reference=reference
                    )
                    if payment.status != "success":
                        payment.status = "success"
                        payment.paid_at = timezone.now()
                        payment.paystack_transaction_id = str(data.get("id", ""))
                        payment.paystack_payload = data
                        payment.save(update_fields=[
                            "status", "paid_at", "paystack_transaction_id", "paystack_payload"
                        ])
                        _handle_successful_payment(payment)
                        logger.info(f"Webhook: payment {reference} marked successful.")
                except Payment.DoesNotExist:
                    logger.warning(f"Webhook: payment {reference} not found in DB.")

        # Always return 200 to Paystack so it stops retrying
        return Response({"status": "ok"})


class PaymentHistoryView(APIView):
    """GET /api/v1/payments/history/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(funder=request.user).select_related("pitch", "funder")
        serializer = PaymentSerializer(payments, many=True)
        return Response({"count": payments.count(), "results": serializer.data})


def _handle_successful_payment(payment: Payment):
    """
    Post-payment business logic:
    - Mark the pitch as funded
    - Accept the linked offer (if any)
    - Reject all other pending offers on the pitch
    """
    pitch = payment.pitch
    if not pitch:
        return

    pitch.funding_status = "funded"
    pitch.save(update_fields=["funding_status"])

    # Accept the linked offer
    if payment.offer and payment.offer.status == "pending":
        payment.offer.status = "accepted"
        payment.offer.save(update_fields=["status", "updated_at"])

    # Reject all other pending offers
    from apps.offers.models import FundingOffer
    qs = FundingOffer.objects.filter(pitch=pitch, status="pending")
    if payment.offer:
        qs = qs.exclude(pk=payment.offer.pk)
    qs.update(status="rejected")

    logger.info(f"Pitch {pitch.id} marked as funded after payment {payment.paystack_reference}.")
