"""
Paystack API client.
Handles transaction initialization, verification, and webhook signature validation.
"""
import hashlib
import hmac
import secrets
import uuid
from decimal import Decimal

import requests
from django.conf import settings


PAYSTACK_BASE_URL = "https://api.paystack.co"
PLATFORM_FEE_RATE = Decimal("0.015")  # 1.5%


def get_headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def generate_reference():
    """Generate a unique transaction reference."""
    return f"GB-{uuid.uuid4().hex[:16].upper()}"


def calculate_fee(amount: Decimal) -> dict:
    """
    Calculate platform fee and total amount.
    Returns amounts in both naira and kobo.
    """
    fee = (amount * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
    total = amount + fee
    total_kobo = int(total * 100)  # Paystack expects kobo
    return {
        "base_amount": amount,
        "platform_fee": fee,
        "total_amount": total,
        "total_kobo": total_kobo,
    }


def initialize_transaction(email: str, amount_kobo: int, reference: str, metadata: dict) -> dict:
    """
    Call Paystack /transaction/initialize.
    Returns { authorization_url, access_code, reference } on success.
    Raises ValueError on failure.
    """
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "metadata": metadata,
        "callback_url": f"{settings.FRONTEND_URL}/dashboard/funder/payment/callback",
    }

    response = requests.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        json=payload,
        headers=get_headers(),
        timeout=30,
    )

    data = response.json()

    if not data.get("status"):
        raise ValueError(data.get("message", "Paystack initialization failed."))

    return data["data"]


def verify_transaction(reference: str) -> dict:
    """
    Call Paystack /transaction/verify/:reference.
    Returns the full transaction data dict.
    Raises ValueError if verification fails or transaction not successful.
    """
    response = requests.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=get_headers(),
        timeout=30,
    )

    data = response.json()

    if not data.get("status"):
        raise ValueError(data.get("message", "Paystack verification failed."))

    return data["data"]


def validate_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    """
    Validate the X-Paystack-Signature header using HMAC-SHA512.
    Returns True if the signature is valid.
    """
    secret = settings.PAYSTACK_SECRET_KEY.encode("utf-8")
    # Python 3: hmac.new() is the correct constructor
    mac = hmac.new(secret, payload_bytes, digestmod=hashlib.sha512)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)