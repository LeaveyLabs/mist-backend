# Generated by Django 4.0.7 on 2022-09-23 04:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0040_user_notification_badge_count_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='notification_badge_count',
        ),
    ]