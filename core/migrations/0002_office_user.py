# Generated by Django 5.1.3 on 2025-01-11 01:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="office",
            name="user",
            field=models.ForeignKey(
                default=1,
                help_text="The user managing this office.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="office",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]
