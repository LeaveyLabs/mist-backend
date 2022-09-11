# Generated by Django 4.0.7 on 2022-09-09 07:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mist', '0063_alter_commentflag_rating_alter_commentvote_rating_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='blocked_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='block',
            name='blocking_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blockings', to=settings.AUTH_USER_MODEL),
        ),
    ]