# Generated by Django 4.0.7 on 2022-09-25 00:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0074_alter_post_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_matched',
            field=models.BooleanField(default=False),
        ),
    ]
