from django.db import models
from django_extensions.db.models import TimeStampedModel


class ListingSource(models.TextChoices):
    OTOMOTO = "otomoto", "Otomoto"
    AUTOSCOUT24 = "autoscout24", "AutoScout24"


class CarOffer(TimeStampedModel):
    """Car listing from a supported marketplace (see ListingSource)."""

    source = models.CharField(
        max_length=32,
        choices=ListingSource.choices,
        db_index=True,
    )
    external_listing_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Platform-specific stable id (Otomoto advert id, AutoScout24 listing UUID, …).",
    )
    public_slug = models.CharField(
        max_length=32,
        blank=True,
        help_text="Otomoto: short ID from URL, e.g. ID6HSO0m",
    )
    url = models.URLField(max_length=1024)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)

    price_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_currency = models.CharField(max_length=8, default="PLN")
    price_labels = models.JSONField(default=list, blank=True)
    price_drop = models.JSONField(null=True, blank=True)
    price_display = models.CharField(max_length=64, blank=True)
    price_tax_deductible = models.BooleanField(null=True, blank=True)

    year = models.PositiveIntegerField(null=True, blank=True)
    mileage_km = models.PositiveIntegerField(null=True, blank=True)
    engine_cc = models.PositiveIntegerField(null=True, blank=True)
    engine_power_hp = models.PositiveIntegerField(null=True, blank=True)
    engine_power_kw = models.PositiveIntegerField(null=True, blank=True)
    fuel_type = models.CharField(max_length=64, blank=True)
    gearbox = models.CharField(max_length=64, blank=True)
    transmission = models.CharField(max_length=128, blank=True)
    drive_train = models.CharField(max_length=64, blank=True)
    body_type = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=64, blank=True)
    paint_type = models.CharField(max_length=64, blank=True)
    doors = models.PositiveSmallIntegerField(null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)
    gears = models.PositiveSmallIntegerField(null=True, blank=True)
    co2_g_km = models.PositiveIntegerField(null=True, blank=True)
    fuel_consumption_l100km_combined = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    make = models.CharField(max_length=128, blank=True)
    make_slug = models.CharField(max_length=128, blank=True)
    model = models.CharField(max_length=128, blank=True)
    model_slug = models.CharField(max_length=128, blank=True)
    model_version = models.CharField(max_length=256, blank=True)
    variant = models.CharField(max_length=128, blank=True)

    vin = models.CharField(max_length=17, blank=True)
    country_origin = models.CharField(max_length=128, blank=True)
    date_registration = models.CharField(max_length=128, blank=True)
    first_registration_raw = models.CharField(max_length=32, blank=True)
    first_registration_date = models.DateField(null=True, blank=True)

    damaged = models.BooleanField(null=True, blank=True)
    no_accident = models.BooleanField(null=True, blank=True)
    registered = models.BooleanField(null=True, blank=True)
    service_record = models.BooleanField(null=True, blank=True)
    vat = models.CharField(max_length=64, blank=True)
    new_used = models.CharField(max_length=32, blank=True)
    had_accident = models.BooleanField(null=True, blank=True)
    has_full_service_history = models.BooleanField(null=True, blank=True)
    non_smoking = models.BooleanField(null=True, blank=True)
    previous_owners = models.PositiveSmallIntegerField(null=True, blank=True)
    next_inspection_raw = models.CharField(max_length=32, blank=True)

    seller_type = models.CharField(max_length=32, blank=True)
    seller_name = models.CharField(max_length=256, blank=True)
    seller_contact = models.CharField(max_length=256, blank=True)
    seller_otomoto_id = models.CharField(max_length=32, blank=True)
    seller_uuid = models.CharField(max_length=64, blank=True)
    seller_url = models.URLField(max_length=1024, blank=True)
    seller_website = models.URLField(max_length=1024, blank=True)
    seller_as24_id = models.CharField(max_length=32, blank=True)
    seller_sell_id = models.CharField(max_length=32, blank=True)
    seller_is_dealer = models.BooleanField(null=True, blank=True)
    seller_links = models.JSONField(null=True, blank=True)
    seller_location = models.JSONField(null=True, blank=True)

    image_urls = models.JSONField(default=list, blank=True)
    main_features = models.JSONField(default=list, blank=True)

    listing_created_at = models.DateTimeField(null=True, blank=True)
    listing_updated_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("-listing_created_at", "-created")
        constraints = [
            models.UniqueConstraint(
                fields=("source", "external_listing_id"),
                name="offers_caroffer_source_external_id_uniq",
            ),
        ]

    def __str__(self):
        return "{} [{}] {}".format(self.title, self.source, self.external_listing_id)
