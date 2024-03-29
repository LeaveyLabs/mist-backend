# Generated by Django 4.0.7 on 2022-09-20 00:44

from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_alter_user_date_of_birth_alter_user_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_of_birth',
            field=models.DateField(default=users.generics.get_default_date_of_birth),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(default=users.generics.get_random_email, max_length=254),
        ),
    ]
