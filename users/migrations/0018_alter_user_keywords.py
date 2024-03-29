# Generated by Django 4.0.7 on 2022-08-22 22:23

import django.contrib.postgres.fields
from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_user_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=users.generics.get_empty_keywords, size=5),
        ),
    ]
