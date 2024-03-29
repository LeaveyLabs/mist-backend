# Generated by Django 4.0.7 on 2022-09-04 22:51

import django.contrib.postgres.fields
from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0053_alter_mistbox_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mistbox',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=users.generics.get_empty_keywords, size=10),
        ),
    ]
