# Generated by Django 4.0.5 on 2022-06-16 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0015_message_post_alter_favorite_unique_together'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='text',
            new_name='body',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='text',
            new_name='body',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='text',
            new_name='body',
        ),
        migrations.RenameField(
            model_name='word',
            old_name='text',
            new_name='body',
        ),
    ]