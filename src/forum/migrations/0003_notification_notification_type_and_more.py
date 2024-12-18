# Generated by Django 5.1.1 on 2024-11-11 21:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forum", "0002_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(default="comment", max_length=20),
        ),
        migrations.AlterField(
            model_name="notification",
            name="comment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="forum.comment",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="post",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="forum.post",
            ),
        ),
    ]
