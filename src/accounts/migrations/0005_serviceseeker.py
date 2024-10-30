# Generated by Django 5.1.1 on 2024-10-29 03:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_merge_20241029_0024"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceSeeker",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=150, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "bookmarked_services",
                    models.JSONField(blank=True, default=list, null=True),
                ),
                (
                    "location_preference",
                    models.CharField(
                        help_text="Preferred borough or location in NYC", max_length=255
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]