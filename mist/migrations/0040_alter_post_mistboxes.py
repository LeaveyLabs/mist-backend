# Generated by Django 4.0.7 on 2022-09-02 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0039_post_mistboxes_delete_mistboxpost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='mistboxes',
            field=models.ManyToManyField(blank=True, null=True, related_name='posts', to='mist.mistbox'),
        ),
    ]
