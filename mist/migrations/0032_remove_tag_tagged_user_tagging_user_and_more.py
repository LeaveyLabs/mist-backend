# Generated by Django 4.0.6 on 2022-08-07 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0031_alter_tag_unique_together'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='tag',
            name='tagged_user_tagging_user',
        ),
        migrations.RemoveConstraint(
            model_name='tag',
            name='tagged_phone_number_tagging_user',
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=('comment', 'tagged_user', 'tagging_user'), name='tagged_user_tagging_user'),
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=('comment', 'tagged_phone_number', 'tagging_user'), name='tagged_phone_number_tagging_user'),
        ),
    ]