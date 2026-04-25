from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0006_car_offer_price_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="caroffer",
            name="listing_availability",
            field=models.CharField(
                choices=[
                    ("unknown", "Nieznana (nie sprawdzono)"),
                    ("active", "Aktywne (ostatni crawl OK)"),
                    ("expired", "Wygasłe / usunięte (404, 410, brak danych)"),
                ],
                db_index=True,
                default="unknown",
                help_text="Otomoto: 404/410 lub brak advertu → wygasłe. Udany zapis z crawla → aktywne.",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="caroffer",
            name="listing_checked_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Ostatni sprawdzony fetch HTTP albo udany parse strony oferty.",
            ),
        ),
    ]
