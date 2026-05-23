from django.contrib import admin
from .models import FundingOffer


@admin.register(FundingOffer)
class FundingOfferAdmin(admin.ModelAdmin):
    list_display = ["funder", "pitch", "amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["funder__email", "funder__full_name", "pitch__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
