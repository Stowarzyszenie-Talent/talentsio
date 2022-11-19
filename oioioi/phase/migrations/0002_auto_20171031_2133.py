# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-10-31 21:33
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='phase',
            options={'ordering': ['start_date'], 'verbose_name': 'phase', 'verbose_name_plural': 'phases'},
        ),
        migrations.AlterField(
            model_name='phase',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contests.Round', verbose_name='round'),
        ),
    ]
