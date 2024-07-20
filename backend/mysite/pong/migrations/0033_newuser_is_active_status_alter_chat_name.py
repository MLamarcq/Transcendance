# Generated by Django 5.0.6 on 2024-07-20 14:27

import shortuuid.main
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pong', '0032_alter_chat_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='newuser',
            name='is_active_status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='chat',
            name='name',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=255, unique=True),
        ),
    ]
