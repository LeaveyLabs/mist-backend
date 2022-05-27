# Generated by Django 4.0.4 on 2022-05-19 20:16

from django.db import migrations, models
import mist.models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0003_delete_account_delete_emailauthentication_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='timestamp',
            field=models.FloatField(default=mist.models.get_current_time),
        ),
        migrations.AlterField(
            model_name='flag',
            name='timestamp',
            field=models.FloatField(default=mist.models.get_current_time),
        ),
        migrations.AlterField(
            model_name='message',
            name='timestamp',
            field=models.FloatField(default=mist.models.get_current_time),
        ),
        migrations.AlterField(
            model_name='post',
            name='timestamp',
            field=models.FloatField(default=mist.models.get_current_time),
        ),
        migrations.AlterField(
            model_name='vote',
            name='timestamp',
            field=models.FloatField(default=mist.models.get_current_time),
        ),
    ]