# Generated by Django 4.0.7 on 2022-09-09 04:25

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_remove_user_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=users.models.User.confirm_profile_picture_filepath),
        ),
    ]
