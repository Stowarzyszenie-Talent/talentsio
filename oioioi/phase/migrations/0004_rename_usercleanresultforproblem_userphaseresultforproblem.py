# Generated by Django 4.2.7 on 2023-12-14 19:52

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contests', '0017_merge_20230615_1827'),
        ('phase', '0003_userfirstphaseresultforproblem_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserCleanResultForProblem',
            new_name='UserPhaseResultForProblem',
        ),
    ]
