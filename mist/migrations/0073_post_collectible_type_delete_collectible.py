# Generated by Django 4.0.7 on 2022-09-22 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0072_collectible_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='collectible_type',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='Collectible',
        ),
    ]
