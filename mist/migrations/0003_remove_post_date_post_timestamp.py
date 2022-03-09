# Generated by Django 4.0.3 on 2022-03-09 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0002_alter_post_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='date',
        ),
        migrations.AddField(
            model_name='post',
            name='timestamp',
            field=models.FloatField(default=0),
        ),
    ]