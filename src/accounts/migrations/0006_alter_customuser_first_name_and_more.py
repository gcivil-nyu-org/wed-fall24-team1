# Generated by Django 5.1.1 on 2024-10-30 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_serviceseeker"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="first_name",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="last_name",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.DeleteModel(
            name="ServiceSeeker",
        ),
    ]
