# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-11-21 23:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='login',
            field=models.CharField(max_length=50, verbose_name='login'),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=50, verbose_name='team name'),
        ),
    ]
