# Generated by Django 4.0.7 on 2022-09-09 04:49

from django.db import migrations


def save_thumbnails_for_all_users(apps, schema_editor):
    from sorl.thumbnail import get_thumbnail
    from django.core.files.base import ContentFile

    User = apps.get_model("users", "User")
    for user in User.objects.all():
        if user.picture:
            user.save()
            resized = get_thumbnail(user.picture, '100x100', quality=99)
            user.thumbnail.save(resized.name, ContentFile(resized.read()), True)
            user.save()
    return



class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_auto_20220909_0444'),
    ]

    operations = [
        migrations.RunPython(save_thumbnails_for_all_users, migrations.RunPython.noop),
    ]
