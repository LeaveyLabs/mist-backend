# Generated by Django 4.0.5 on 2022-06-26 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sex',
            field=models.CharField(choices=[('m', 'm'), ('f', 'f')], max_length=1, null=True),
        ),
    ]
