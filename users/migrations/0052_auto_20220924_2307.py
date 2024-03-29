# Generated by Django 4.0.7 on 2022-09-24 23:07

from django.db import migrations

def reset_thumbnail_and_prompts_for_all_users(apps, schema_editor):
    from users.generics import get_empty_prompts

    User = apps.get_model("users", "User")
    for user in User.objects.all():
        user.daily_prompts = get_empty_prompts()
        user.save()
    return


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0051_user_is_test_user'),
    ]

    operations = [
        migrations.RunPython(reset_thumbnail_and_prompts_for_all_users, migrations.RunPython.noop),
    ]
