# Generated manually: single CarOffer table with ListingSource + data from AutoScout24Offer

from django.db import migrations, models


def backfill_external_listing_id(apps, schema_editor):
    CarOffer = apps.get_model("offers", "CarOffer")
    for row in CarOffer.objects.all():
        row.external_listing_id = (row.otomoto_ad_id or "")[:64]
        row.save(update_fields=["external_listing_id"])


def merge_autoscout24_into_caroffer(apps, schema_editor):
    AutoScout24Offer = apps.get_model("offers", "AutoScout24Offer")
    CarOffer = apps.get_model("offers", "CarOffer")
    for row in AutoScout24Offer.objects.all():
        CarOffer.objects.create(
            source="autoscout24",
            external_listing_id=row.listing_guid,
            public_slug="",
            url=row.url,
            title=row.title,
            description=row.description,
            price_amount=row.price_amount,
            price_currency=row.price_currency,
            price_labels=[],
            price_drop=None,
            price_display=row.price_display or "",
            price_tax_deductible=row.price_tax_deductible,
            mileage_km=row.mileage_km,
            first_registration_raw=row.first_registration_raw or "",
            first_registration_date=row.first_registration_date,
            year=row.production_year,
            fuel_type=row.fuel_type or "",
            gearbox="",
            transmission=row.transmission or "",
            drive_train=row.drive_train or "",
            body_type=row.body_type or "",
            color=row.color or "",
            paint_type=row.paint_type or "",
            doors=row.doors,
            seats=row.seats,
            engine_cc=row.engine_cc,
            engine_power_hp=row.engine_power_hp,
            engine_power_kw=row.engine_power_kw,
            gears=row.gears,
            co2_g_km=row.co2_g_km,
            fuel_consumption_l100km_combined=row.fuel_consumption_l100km_combined,
            make=row.make or "",
            make_slug="",
            model=row.model or "",
            model_slug="",
            model_version=row.model_version or "",
            variant=row.variant or "",
            vin=row.vin or "",
            country_origin="",
            date_registration="",
            damaged=None,
            no_accident=None,
            registered=None,
            service_record=None,
            vat="",
            new_used="",
            had_accident=row.had_accident,
            has_full_service_history=row.has_full_service_history,
            non_smoking=row.non_smoking,
            previous_owners=row.previous_owners,
            next_inspection_raw=row.next_inspection_raw or "",
            seller_type=row.seller_type or "",
            seller_name=row.seller_company or "",
            seller_contact=row.seller_contact or "",
            seller_otomoto_id="",
            seller_uuid="",
            seller_url="",
            seller_website="",
            seller_as24_id=row.seller_as24_id or "",
            seller_sell_id=row.seller_sell_id or "",
            seller_is_dealer=row.seller_is_dealer,
            seller_links=row.seller_links,
            seller_location=row.location,
            image_urls=row.image_urls if row.image_urls is not None else [],
            main_features=[],
            listing_created_at=row.listing_created_at,
            listing_updated_at=None,
            raw_payload=row.raw_listing,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0002_autoscout24_offer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caroffer",
            name="otomoto_ad_id",
            field=models.CharField(db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="source",
            field=models.CharField(
                choices=[("otomoto", "Otomoto"), ("autoscout24", "AutoScout24")],
                db_index=True,
                default="otomoto",
                max_length=32,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="caroffer",
            name="external_listing_id",
            field=models.CharField(
                db_index=True,
                help_text="Platform-specific stable id (Otomoto advert id, AutoScout24 listing UUID, …).",
                max_length=64,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_external_listing_id, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="caroffer",
            old_name="otomoto_created_at",
            new_name="listing_created_at",
        ),
        migrations.RenameField(
            model_name="caroffer",
            old_name="otomoto_updated_at",
            new_name="listing_updated_at",
        ),
        migrations.RenameField(
            model_name="caroffer",
            old_name="raw_advert",
            new_name="raw_payload",
        ),
        migrations.AddField(
            model_name="caroffer",
            name="price_display",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="price_tax_deductible",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="first_registration_raw",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="first_registration_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="engine_power_kw",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="drive_train",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="paint_type",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="gears",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="co2_g_km",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="fuel_consumption_l100km_combined",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="model_version",
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="variant",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="had_accident",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="has_full_service_history",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="non_smoking",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="previous_owners",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="next_inspection_raw",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="seller_contact",
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="seller_as24_id",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="seller_sell_id",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="seller_is_dealer",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="seller_links",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.RunPython(merge_autoscout24_into_caroffer, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="AutoScout24Offer",
        ),
        migrations.RemoveField(
            model_name="caroffer",
            name="otomoto_ad_id",
        ),
        migrations.AlterField(
            model_name="caroffer",
            name="external_listing_id",
            field=models.CharField(
                db_index=True,
                help_text="Platform-specific stable id (Otomoto advert id, AutoScout24 listing UUID, …).",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="caroffer",
            name="vin",
            field=models.CharField(blank=True, max_length=17),
        ),
        migrations.AlterModelOptions(
            name="caroffer",
            options={"ordering": ("-listing_created_at", "-created")},
        ),
        migrations.AddConstraint(
            model_name="caroffer",
            constraint=models.UniqueConstraint(
                fields=("source", "external_listing_id"),
                name="offers_caroffer_source_external_id_uniq",
            ),
        ),
    ]
