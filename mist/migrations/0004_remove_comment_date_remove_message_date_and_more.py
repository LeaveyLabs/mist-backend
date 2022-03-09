# Generated by Django 4.0.3 on 2022-03-09 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0003_remove_post_date_post_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='date',
        ),
        migrations.RemoveField(
            model_name='message',
            name='date',
        ),
        migrations.AddField(
            model_name='comment',
            name='timestamp',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='message',
            name='timestamp',
            field=models.FloatField(default=0),
        ),
    ]