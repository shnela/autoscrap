from django.contrib import admin

from offers.models import AutoScout24Offer, CarOffer


@admin.register(CarOffer)
class CarOfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "otomoto_ad_id",
        "public_slug",
        "price_amount",
        "price_currency",
        "year",
        "mileage_km",
        "make",
        "model",
        "seller_name",
        "otomoto_created_at",
        "modified",
    )
    list_filter = ("make", "fuel_type", "gearbox", "seller_type", "year")
    search_fields = ("title", "otomoto_ad_id", "public_slug", "description", "url", "seller_name")
    readonly_fields = ("created", "modified", "raw_advert")
    date_hierarchy = "otomoto_created_at"


@admin.register(AutoScout24Offer)
class AutoScout24OfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "listing_guid",
        "price_amount",
        "price_currency",
        "mileage_km",
        "production_year",
        "make",
        "model",
        "seller_company",
        "listing_created_at",
        "modified",
    )
    list_filter = ("make", "fuel_type", "transmission", "seller_type", "production_year")
    search_fields = ("title", "listing_guid", "description", "url", "seller_company", "vin")
    readonly_fields = ("created", "modified", "raw_listing")
    date_hierarchy = "listing_created_at"
