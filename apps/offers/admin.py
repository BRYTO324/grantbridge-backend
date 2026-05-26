from django.contrib import admin
from django.utils.html import format_html
from .models import FundingOffer


@admin.register(FundingOffer)
class FundingOfferAdmin(admin.ModelAdmin):
    list_display = ["funder", "pitch", "amount_display", "status_badge", "created_at"]
    list_filter = ["status"]
    search_fields = ["funder__email", "funder__full_name", "pitch__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25

    actions = ["accept_offers", "reject_offers"]

    def accept_offers(self, request, queryset):
        for offer in queryset.filter(status="pending"):
            offer.status = "accepted"
            offer.save()
            offer.pitch.funding_status = "funded"
            offer.pitch.save(update_fields=["funding_status"])
            # Reject other pending offers on same pitch
            FundingOffer.objects.filter(
                pitch=offer.pitch, status="pending"
            ).exclude(pk=offer.pk).update(status="rejected")
        self.message_user(request, "Selected offers accepted.")
    accept_offers.short_description = "✅ Accept selected offers"

    def reject_offers(self, request, queryset):
        queryset.filter(status="pending").update(status="rejected")
        self.message_user(request, "Selected offers rejected.")
    reject_offers.short_description = "❌ Reject selected offers"

    def amount_display(self, obj):
        return f"₦{obj.amount:,.0f}"
    amount_display.short_description = "Amount"

    def status_badge(self, obj):
        colors = {"pending": "#f59e0b", "accepted": "#10b981", "rejected": "#ef4444"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = "Status"
