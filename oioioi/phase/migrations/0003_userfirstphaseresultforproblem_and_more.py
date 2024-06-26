# Generated by Django 4.2.3 on 2023-07-14 10:07

from datetime import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import make_aware
import oioioi.contests.fields
from oioioi.contests.scores import IntegerScore


# This is the best (in terms of solidness) solution I could come up with
class _LastPhase:
    multiplier = 0
    start_date = make_aware(datetime(9000, 1, 1))


def update_user_result_for_problem(apps, schema_editor, result):
    Submission = apps.get_model('contests', 'Submission')
    SubmissionReport = apps.get_model('contests', 'SubmissionReport')
    UserResultForProblem = apps.get_model('contests', 'UserResultForProblem')
    UserCleanResultForProblem = apps.get_model('phase', 'UserCleanResultForProblem')
    UserFirstPhaseResultForProblem = apps.get_model('phase', 'UserFirstPhaseResultForProblem')
    Phase = apps.get_model('phase', 'Phase')
    user = result.user
    pi = result.problem_instance
    clean_result, _ = UserCleanResultForProblem.objects.select_for_update(
    ).get_or_create(user=user, problem_instance=pi)
    first_phase_result, _ = UserFirstPhaseResultForProblem.objects.select_for_update(
    ).get_or_create(user=user, problem_instance=pi)

    base_qs = Submission.objects.filter(
        problem_instance=pi,
        user=result.user,
        score__isnull=False,
        kind='NORMAL'
    ).exclude(status='CE').order_by('date')

    phases = list(Phase.objects.filter(
        round_id=pi.round_id,
    ).order_by('start_date')) + [_LastPhase,]

    highest = 0
    total = 0
    # First phase
    prev_multiplier = 100

    for p in phases:
        s = base_qs.filter(date__lt=p.start_date).last()
        if s:
            total += prev_multiplier * max(s.score.to_int() - highest, 0)
            highest = max(highest, s.score.to_int())
        prev_multiplier = p.multiplier

    first_phase_sub = base_qs.filter(date__lt=phases[0].start_date).last()
    first_phase_result.score = first_phase_sub.score if first_phase_sub else None

    last_submission = base_qs.last()
    if last_submission: # if there are any meaningful submissions
        report = SubmissionReport.objects.filter(
            submission=last_submission, status='ACTIVE', kind='NORMAL'
        ).last()

        result.score = IntegerScore(total // 100)
        result.status = last_submission.status
        result.submission_report = report
        clean_result.score = IntegerScore(highest)
    else:
        result.score = None
        result.status = None
        result.submission_report = None
        clean_result.score = None

    result.save()
    clean_result.save()
    first_phase_result.save()


def recalc_user_results(apps, schema_editor):
    Contest = apps.get_model('contests', 'Contest')
    UserResultForProblem = apps.get_model('contests', 'UserResultForProblem')
    for c in Contest.objects.all():
        if c.controller_name in (
            'oioioi.talent.controllers.TalentOpenContestController',
            'oioioi.talent.controllers.TalentContestController',
        ):
            # Only these should be meaningful
            for result in UserResultForProblem.objects.filter(
                problem_instance__contest_id=c.id
            ).select_related('user', 'problem_instance'):
                update_user_result_for_problem(apps, schema_editor, result)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contests', '0017_merge_20230615_1827'),
        ('phase', '0002_auto_20171031_2133'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFirstPhaseResultForProblem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', oioioi.contests.fields.ScoreField(blank=True, max_length=255, null=True)),
                ('problem_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contests.probleminstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'problem_instance')},
            },
        ),
        migrations.CreateModel(
            name='UserCleanResultForProblem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', oioioi.contests.fields.ScoreField(blank=True, max_length=255, null=True)),
                ('problem_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contests.probleminstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'problem_instance')},
            },
        ),
        migrations.RunPython(recalc_user_results, reverse_code=noop),
    ]
