# Generated by Django 4.2.11 on 2024-04-23 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0017_contest_is_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='show_contest_rules',
            field=models.BooleanField(default=True, verbose_name='show contest rules'),
        ),
    ]
