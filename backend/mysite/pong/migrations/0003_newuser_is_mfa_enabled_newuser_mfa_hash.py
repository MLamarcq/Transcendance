# Generated by Django 5.0.6 on 2024-06-22 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pong', '0002_newuser_is_active_newuser_is_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='newuser',
            name='is_mfa_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='newuser',
            name='mfa_hash',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
