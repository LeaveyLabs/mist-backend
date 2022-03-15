# Generated by Django 4.0.3 on 2022-03-15 06:09

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0016_post_latitude_post_longitude'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='location',
        ),
        migrations.AlterField(
            model_name='post',
            name='latitude',
            field=models.DecimalField(decimal_places=16, default=Decimal('34.02239999999999753299562144093215465545654296875'), max_digits=22, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='longitude',
            field=models.DecimalField(decimal_places=16, default=Decimal('118.28509999999999990905052982270717620849609375'), max_digits=22, null=True),
        ),
    ]
