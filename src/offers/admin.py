from django.contrib import admin

from offers.admin_filters import (
    CarOfferFeatureFilters,
    MileageFromFilter,
    MileageToFilter,
)
from offers.models import CarOffer


@admin.register(CarOffer)
class CarOfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "year",
        "fuel_type",
        "wheel_size",
        "engine_model",
        "color",
        "upholstery_color",
        "audio_system",
        "headlight_quality",
        "feature_awd",
        "feature_pneumatic_suspension",
        "feature_panoramic_roof",
        "feature_pilot_assist",
        "is_first_owner",
        "service_record",
        "price_pln_display",
        "mileage_km",
        "vin",
        "make",
        "model",
        "listing_location",
        "seller_name",
        "listing_created_at",
        "modified",
    )
    list_filter = (
        MileageFromFilter,
        MileageToFilter,
        "source",
        "year",
        "audio_system",
        "headlight_quality",
        "make",
        "fuel_type",
        "wheel_size",
        "model",
        "engine_model",
        "color",
        "upholstery_color",
        "gearbox",
        "transmission",
        "drive_train",
        "body_type",
        "seller_type",
        *CarOfferFeatureFilters,
    )
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

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "source",
                    "external_listing_id",
                    "public_slug",
                    "url",
                    "title",
                    "description",
                    "year",
                    "listing_created_at",
                    "listing_updated_at",
                )
            },
        ),
        (
            "Price",
            {
                "fields": (
                    "price_amount",
                    "price_currency",
                    "price_display",
                    "price_labels",
                    "price_drop",
                    "price_tax_deductible",
                )
            },
        ),
        (
            "Vehicle",
            {
                "fields": (
                    "make",
                    "make_slug",
                    "model",
                    "model_slug",
                    "model_version",
                    "variant",
                    "mileage_km",
                    "vin",
                    "fuel_type",
                    "wheel_size",
                    "engine_model",
                    "gearbox",
                    "transmission",
                    "drive_train",
                    "body_type",
                    "color",
                    "upholstery_color",
                    "paint_type",
                    "doors",
                    "seats",
                    "engine_cc",
                    "engine_power_hp",
                    "engine_power_kw",
                    "gears",
                    "co2_g_km",
                    "fuel_consumption_l100km_combined",
                    "first_registration_raw",
                    "first_registration_date",
                    "date_registration",
                    "country_origin",
                    "listing_location",
                )
            },
        ),
        (
            "History & condition",
            {
                "fields": (
                    "damaged",
                    "had_accident",
                    "no_accident",
                    "registered",
                    "service_record",
                    "has_full_service_history",
                    "non_smoking",
                    "previous_owners",
                    "next_inspection_raw",
                    "vat",
                    "new_used",
                )
            },
        ),
        (
            "Drivetrain & chassis (features)",
            {
                "classes": ("collapse",),
                "fields": (
                    "feature_awd",
                    "feature_increased_clearance_off_road_mode",
                    "feature_hill_descent_control",
                    "feature_rear_air_suspension",
                    "feature_pneumatic_suspension",
                ),
            },
        ),
        (
            "Safety & assistance (features)",
            {
                "classes": ("collapse",),
                "fields": (
                    "feature_pilot_assist",
                    "feature_city_safety",
                    "feature_cross_traffic_alert_reverse_brake",
                    "feature_surround_view_camera_360",
                    "feature_front_rear_parking_sensors",
                    "headlight_quality",
                ),
            },
        ),
        (
            "Comfort & interior (features)",
            {
                "classes": ("collapse",),
                "fields": (
                    "feature_panoramic_roof",
                    "feature_four_zone_climate",
                    "feature_power_tailgate",
                    "feature_remote_rear_seatback_release",
                    "feature_folding_rear_headrests",
                ),
            },
        ),
        (
            "Audio & infotainment (features)",
            {
                "classes": ("collapse",),
                "fields": (
                    "audio_system",
                    "feature_google_built_in_infotainment",
                ),
            },
        ),
        (
            "Luxury trim (features)",
            {
                "classes": ("collapse",),
                "fields": (
                    "feature_wood_or_metal_inlays",
                    "feature_crystal_gear_selector",
                    "feature_ambient_lighting_package",
                ),
            },
        ),
        (
            "Seller & media",
            {
                "classes": ("collapse",),
                "fields": (
                    "seller_type",
                    "seller_name",
                    "seller_contact",
                    "seller_otomoto_id",
                    "seller_uuid",
                    "seller_url",
                    "seller_website",
                    "seller_as24_id",
                    "seller_sell_id",
                    "seller_is_dealer",
                    "seller_links",
                    "seller_location",
                    "image_urls",
                    "main_features",
                )
            },
        ),
        (
            "Raw & timestamps",
            {
                "classes": ("collapse",),
                "fields": ("raw_payload", "created", "modified"),
            },
        ),
    )

    @admin.display(boolean=True, ordering="previous_owners", description="First owner")
    def is_first_owner(self, obj):
        if obj.previous_owners is None:
            return None
        return obj.previous_owners <= 1

    @admin.display(description="Price PLN")
    def price_pln_display(self, obj):
        if obj.price_pln is None:
            return None
        return f"{obj.price_pln}"
