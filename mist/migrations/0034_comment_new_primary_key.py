# Generated by Django 4.0.4 on 2022-05-15 23:18

from django.db import migrations, models

def create_ids(apps, schema_editor):
    Comment = apps.get_model('mist', 'Comment')
    comments = Comment.objects.all()
    i = 1
    for c in comments:
        c.id = i
        i += 1
        c.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mist', '0033_word_posts_alter_word_text'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='id',
            new_name='uuid',
        ),
        migrations.AddField(
            model_name='comment',
            name='id',
            field=models.BigIntegerField(null=True)
        ),
        migrations.RunPython(
            code=create_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='comment',
            name='uuid',
            field=models.CharField(max_length=36, unique=True)
        ),     
        migrations.AlterField(
            model_name='comment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),

    ]