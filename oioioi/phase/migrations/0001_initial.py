# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0005_auto_20150531_2248'),
    ]

    operations = [
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('multiplier', models.IntegerField(verbose_name='phase multiplier')),
                ('round', models.ForeignKey(to='contests.Round', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Phase',
                'verbose_name_plural': 'Phases',
            },
            bases=(models.Model,),
        ),
    ]
