# Manually created

from datetime import datetime

from django.db import migrations
from django.utils.timezone import make_aware
from oioioi.contests.scores import IntegerScore


# This is the best (in terms of solidness) solution I could come up with
class _LastPhase:
    multiplier = 0
    start_date = make_aware(datetime(9000, 1, 1))


# Swaps UserResult... with UserPhaseResult..., as previously the former had
# phase multipliers applied, but after the UserCleanResult ->UserPhaseResult
# rename that is no longer the case.
def swap_user_result_for_problem(apps, schema_editor, result):
    Submission = apps.get_model('contests', 'Submission')
    SubmissionReport = apps.get_model('contests', 'SubmissionReport')
    UserResultForProblem = apps.get_model('contests', 'UserResultForProblem')
    UserPhaseResultForProblem = apps.get_model('phase', 'UserPhaseResultForProblem')

    phase_result, _ = UserPhaseResultForProblem.objects.select_for_update(
    ).get_or_create(user=result.user, problem_instance=result.problem_instance)

    tmp_score = result.score
    result.score = phase_result.score
    phase_result.score = tmp_score

    result.save()
    phase_result.save()


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
                swap_user_result_for_problem(apps, schema_editor, result)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0004_rename_usercleanresultforproblem_userphaseresultforproblem'),
    ]

    operations = [
        migrations.RunPython(recalc_user_results, reverse_code=noop),
    ]
