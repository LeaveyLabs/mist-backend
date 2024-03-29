# Generated by Django 4.0.7 on 2022-08-30 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_alter_phonenumberauthentication_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='is_validated',
            new_name='is_verified',
        ),
        migrations.AlterField(
            model_name='phonenumberauthentication',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]
