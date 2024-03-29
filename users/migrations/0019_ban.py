# Generated by Django 4.0.7 on 2022-08-23 19:48

from django.db import migrations, models
import users.generics


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_alter_user_keywords'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ban',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('timestamp', models.FloatField(default=users.generics.get_current_time)),
            ],
        ),
    ]
