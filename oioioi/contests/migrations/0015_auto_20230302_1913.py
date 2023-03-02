# Generated by Django 3.2.18 on 2023-03-02 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0014_contest_enable_editor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='default_submissions_limit',
            field=models.IntegerField(blank=True, default=150, help_text='Use 0 for unlimited submissions.', verbose_name='default submissions limit'),
        ),
        migrations.AlterField(
            model_name='probleminstance',
            name='submissions_limit',
            field=models.IntegerField(default=150, help_text='Use 0 for unlimited submissions.', verbose_name='submissions limit'),
        ),
    ]
