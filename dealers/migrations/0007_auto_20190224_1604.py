# Generated by Django 2.1.7 on 2019-02-24 16:04

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dealers', '0006_auto_20190222_1048'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dealer',
            name='average_ratings',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='company_url',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='geo_lat',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='geo_long',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='ratings_count',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='street',
        ),
        migrations.RemoveField(
            model_name='dealer',
            name='url_name',
        ),
        migrations.AddField(
            model_name='dealer',
            name='autoscout_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
            preserve_default=False,
        ),
    ]
