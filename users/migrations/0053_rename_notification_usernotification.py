# Generated by Django 4.0.7 on 2022-09-26 00:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0052_auto_20220924_2307'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Notification',
            new_name='UserNotification',
        ),
    ]
