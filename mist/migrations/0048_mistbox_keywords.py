# Generated by Django 4.0.7 on 2022-09-04 05:58

import django.contrib.postgres.fields
from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0047_alter_mistbox_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='mistbox',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=users.generics.get_empty_keywords, size=5),
        ),
    ]
