# Generated by Django 4.2.6 on 2023-12-13 15:38

from django.db import migrations, models
import django.db.models.deletion
import oioioi.base.fields
import oioioi.participants.fields


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0011_alter_onsiteregistration_participant_and_more'),
        ('pa', '0002_auto_20181117_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='paregistration',
            name='no_prizes',
            field=models.BooleanField(default=False, verbose_name="I don't want to provide my address (opt out of prizes)"),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='address'),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='city'),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='job',
            field=models.CharField(choices=[('PS', 'Szkoła podstawowa'), ('MS', 'Gimnazjum'), ('HS', 'Szkoła ponadgimnazjalna'), ('OTH', 'Inne'), ('AS', 'Szkoła wyższa - student'), ('AD', 'Szkoła wyższa - doktorant'), ('COM', 'Firma')], max_length=7, verbose_name='job or school kind'),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='participant',
            field=oioioi.participants.fields.OneToOneBothHandsCascadingParticipantField(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s', to='participants.participant'),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='postal_code',
            field=oioioi.base.fields.PostalCodeField(blank=True, null=True, verbose_name='postal code'),
        ),
        migrations.AlterField(
            model_name='paregistration',
            name='t_shirt_size',
            field=models.CharField(blank=True, choices=[('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')], max_length=7, null=True, verbose_name='t-shirt size'),
        ),
    ]
