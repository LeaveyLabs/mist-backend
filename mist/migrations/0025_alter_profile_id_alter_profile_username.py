# Generated by Django 4.0.4 on 2022-05-15 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0024_profile_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='username',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='profile',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]