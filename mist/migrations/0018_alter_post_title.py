# Generated by Django 4.0.5 on 2022-06-22 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0017_rename_body_word_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=50),
        ),
    ]