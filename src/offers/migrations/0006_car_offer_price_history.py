from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_price_history(apps, schema_editor):
    CarOffer = apps.get_model("offers", "CarOffer")
    CarOfferPriceHistory = apps.get_model("offers", "CarOfferPriceHistory")

    now = django.utils.timezone.now()
    rates = {
        "PLN": Decimal("1.00"),
        "EUR": Decimal("4.30"),
    }
    rows = []
    for offer in CarOffer.objects.exclude(price_amount__isnull=True).iterator():
        currency = (offer.price_currency or "PLN").upper()
        rate = rates.get(currency)
        price_pln = None
        if rate is not None:
            try:
                price_pln = (Decimal(offer.price_amount) * rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            except (InvalidOperation, TypeError, ValueError):
                price_pln = None

        rows.append(
            CarOfferPriceHistory(
                offer_id=offer.id,
                price_amount=offer.price_amount,
                price_currency=currency,
                price_pln=price_pln,
                listing_updated_at=offer.listing_updated_at,
                captured_at=now,
            )
        )
    if rows:
        CarOfferPriceHistory.objects.bulk_create(rows, batch_size=1000)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0005_pneumatic_suspension_headlights"),
    ]

    operations = [
        migrations.CreateModel(
            name="CarOfferPriceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                ("price_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("price_currency", models.CharField(default="PLN", max_length=8)),
                ("price_pln", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("listing_updated_at", models.DateTimeField(blank=True, null=True)),
                ("captured_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "offer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="price_history",
                        to="offers.caroffer",
                    ),
                ),
            ],
            options={
                "ordering": ("-captured_at", "-created"),
                "indexes": [models.Index(fields=["offer", "-captured_at"], name="offers_caro_offer_i_5b510f_idx")],
            },
        ),
        migrations.RunPython(backfill_price_history, noop_reverse),
    ]
