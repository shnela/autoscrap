# Generated by Django 4.2.4 on 2023-09-02 18:36

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ("dealers", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dealer",
            name="country",
            field=models.CharField(choices=[("IT", "Italy"), ("F", "France"), ("D", "Germany")], max_length=2),
        ),
    ]
