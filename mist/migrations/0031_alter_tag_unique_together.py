# Generated by Django 4.0.6 on 2022-08-04 06:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0030_remove_tag_mist_tag_thing1_or_thing2_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set(),
        ),
    ]
