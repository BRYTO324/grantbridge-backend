from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "paystack_reference", "funder", "pitch", "amount", "platform_fee",
        "status", "paid_at", "created_at"
    ]
    list_filter = ["status"]
    search_fields = [
        "paystack_reference", "funder__email", "funder__full_name", "pitch__title"
    ]
    readonly_fields = [
        "id", "paystack_reference", "paystack_transaction_id",
        "paystack_authorization_url", "paystack_payload",
        "amount_kobo", "created_at", "updated_at"
    ]
    ordering = ["-created_at"]
