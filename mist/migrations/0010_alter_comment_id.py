# Generated by Django 4.0.3 on 2022-03-13 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0009_alter_flag_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='id',
            field=models.CharField(max_length=10, primary_key=True, serialize=False),
        ),
    ]
