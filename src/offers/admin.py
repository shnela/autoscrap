from django.contrib import admin

from offers.models import CarOffer


@admin.register(CarOffer)
class CarOfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "external_listing_id",
        "public_slug",
        "price_amount",
        "price_currency",
        "year",
        "mileage_km",
        "make",
        "model",
        "seller_name",
        "listing_created_at",
        "modified",
    )
    list_filter = ("source", "make", "fuel_type", "gearbox", "seller_type", "year")
    search_fields = (
        "title",
        "external_listing_id",
        "public_slug",
        "description",
        "url",
        "seller_name",
        "vin",
    )
    readonly_fields = ("created", "modified", "raw_payload")
    date_hierarchy = "listing_created_at"
