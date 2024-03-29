# Generated by Django 4.0.4 on 2022-06-09 16:34

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mist', '0013_matchrequest_post'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='matchrequest',
            unique_together={('match_requesting_user', 'match_requested_user', 'post')},
        ),
    ]
