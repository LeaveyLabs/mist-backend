# Generated by Django 4.0.6 on 2022-08-01 01:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0024_postvote_emoji'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postvote',
            name='emoji',
            field=models.CharField(default='👍', max_length=5),
        ),
    ]
