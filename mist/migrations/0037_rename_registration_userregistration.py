# Generated by Django 4.0.4 on 2022-05-19 04:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0036_alter_comment_uuid'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Registration',
            new_name='UserRegistration',
        ),
    ]