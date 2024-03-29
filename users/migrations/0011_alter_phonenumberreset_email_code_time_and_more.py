# Generated by Django 4.0.6 on 2022-08-10 23:06

from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_phonenumberreset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phonenumberreset',
            name='email_code_time',
            field=models.FloatField(default=users.generics.get_current_time),
        ),
        migrations.AlterField(
            model_name='phonenumberreset',
            name='phone_number_code_time',
            field=models.FloatField(default=users.generics.get_current_time),
        ),
    ]
