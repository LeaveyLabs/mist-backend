# Generated by Django 4.0.6 on 2022-08-10 23:04

from django.db import migrations, models
import phonenumber_field.modelfields
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_emailauthentication_email_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhoneNumberReset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('email_code', models.CharField(default=users.generics.get_random_code, max_length=6)),
                ('email_code_time', models.FloatField(default=users.generics.get_current_time, editable=False)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True)),
                ('phone_number_code', models.CharField(default=users.generics.get_random_code, max_length=6)),
                ('phone_number_code_time', models.FloatField(default=users.generics.get_current_time, editable=False)),
                ('validated', models.BooleanField(default=False)),
                ('validation_time', models.FloatField(null=True)),
            ],
        ),
    ]
