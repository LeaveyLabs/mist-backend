# Generated by Django 4.0.7 on 2022-09-17 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0068_alter_post_longitude'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='location_description',
            field=models.CharField(default='usc', max_length=40),
        ),
    ]
