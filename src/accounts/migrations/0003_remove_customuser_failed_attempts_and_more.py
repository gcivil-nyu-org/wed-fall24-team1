# Generated by Django 5.1.1 on 2024-10-23 04:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_customuser_failed_attempts_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="failed_attempts",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="last_failed_attempt",
        ),
    ]
