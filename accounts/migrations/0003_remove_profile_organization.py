# Generated by Django 5.1.4 on 2025-01-25 00:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="organization",
        ),
    ]
