# Generated by Django 4.2.9 on 2024-02-11 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0006_talentregistration_room'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talentregistration',
            name='room',
            field=models.CharField(max_length=15, null=True, verbose_name='room_number_short_desc'),
        ),
    ]
