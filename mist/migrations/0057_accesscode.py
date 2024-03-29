# Generated by Django 4.0.7 on 2022-09-05 17:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import users.generics


def generate_starter_access_codes(apps, schema_editor):
    NUMBER_OF_INITIAL_CODES = 2000
    AccessCode = apps.get_model("mist", "AccessCode")
    for _ in range(NUMBER_OF_INITIAL_CODES):
        new_code = users.generics.get_random_code()
        while AccessCode.objects.filter(code_string=new_code):
            new_code = users.generics.get_random_code()
        AccessCode.objects.create(code_string=new_code)

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mist', '0056_rename_swipecount_mistbox_opens_used_today'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessCode',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'code_string',
                    models.CharField(
                        default=users.generics.get_random_code, max_length=6, unique=True
                    ),
                ),
                (
                    'claimed_user',
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='access_code',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(generate_starter_access_codes, migrations.RunPython.noop),
    ]
