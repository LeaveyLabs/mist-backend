# Generated by Django 4.0.7 on 2022-08-31 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_alter_user_confirm_picture_alter_user_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]
