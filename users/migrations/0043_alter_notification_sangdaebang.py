# Generated by Django 4.0.7 on 2022-09-23 06:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0042_remove_usermessageactivity_sangdaebang_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='sangdaebang',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
