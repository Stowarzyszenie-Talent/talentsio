from datetime import datetime

from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

from oioioi.contests.models import (
    Submission,
    SubmissionReport,
    UserResultForProblem,
)
from oioioi.contests.scores import IntegerScore
from oioioi.phase.models import (
    Phase,
    UserPhaseResultForProblem,
    UserFirstPhaseResultForProblem,
)
from oioioi.rankings.controllers import DefaultRankingController

class _FirstPhase:
    multiplier = 100
    start_date = make_aware(datetime(1984, 1, 1))

class _LastPhase:
    multiplier = 0
    start_date = make_aware(datetime(9000, 1, 1))

class PhaseMixinForContestController(object):
    is_phase_contest = True

    def update_user_result_for_problem(self, result):
        # Because of mixins there isn't really a better place for this
        user = result.user
        pi = result.problem_instance
        phase_result, _ = UserPhaseResultForProblem.objects.select_for_update(
        ).get_or_create(user=user, problem_instance=pi)
        first_phase_result, _ = UserFirstPhaseResultForProblem.objects. \
            select_for_update().get_or_create(user=user, problem_instance=pi)

        base_qs = Submission.objects.filter(
            problem_instance=pi,
            user=user,
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
                total += prev_multiplier * max(
                    s.score.to_int() - highest, 0)
                highest = max(highest, s.score.to_int())
            prev_multiplier = p.multiplier

        first_phase_sub = base_qs.filter(
            date__lt=phases[0].start_date).last()
        first_phase_result.score = None
        if first_phase_sub:
            first_phase_result.score = first_phase_sub.score

        last_submission = base_qs.last()
        if last_submission: # if there are any meaningful submissions
            report = SubmissionReport.objects.filter(
                submission=last_submission, status='ACTIVE', kind='NORMAL'
            ).last()

            result.score = IntegerScore(highest)
            result.status = last_submission.status
            result.submission_report = report
            phase_result.score = IntegerScore(total // 100)
        else:
            result.score = None
            result.status = None
            result.submission_report = None
            phase_result.score = None

        result.save()
        phase_result.save()
        first_phase_result.save()


class PhaseRankingController(DefaultRankingController):
    """ We want 3 separate rankings: the default one, one with all phases'
    multipliers set to 100 and one with only the first phase.
    """
    description = _("Talent's phase ranking")
    RANKING_TYPES = ['default', 'first', 'clean',] # [0] needs to be the default
    BASE_QUERYSETS = {
        'default': UserPhaseResultForProblem.objects.all(),
        'first': UserFirstPhaseResultForProblem.objects.all(),
        'clean': UserResultForProblem.objects.all(
            ).select_related('submission_report'),
    }
    TYPE_NAMES = {
        'default': _("Default"),
        'first': _("First phase only"),
        'clean': _("Without multipliers"),
    }

    def get_perm(self, request):
        for checker in self.PERMISSION_CHECKERS:
            res = checker(request)
            if res is not None:
                return res

    def get_type(self, request):
        rtype = None
        if 'ranking_type' in getattr(request, 'session', {}):
            rtype = request.session['ranking_type'].get(
                request.contest.id, None)
        # Fail silently
        if rtype not in self.RANKING_TYPES:
            rtype = self.RANKING_TYPES[0]
        return rtype

    def construct_full_key(self, perm_level, partial_key):
        raise NotImplementedError

    def construct_full_key(self, perm_level, rtype, partial_key):
        return perm_level + '.' + rtype + '#' + partial_key

    def get_full_key(self, request, partial_key):
        return self.construct_full_key(
            self.get_perm(request),
            self.get_type(request),
            partial_key,
        )

    def construct_all_full_keys(self, partial_keys):
        fulls = []
        for perm in self.PERMISSION_LEVELS:
            for rtype in self.RANKING_TYPES:
                for partial in partial_keys:
                    fulls.append(self.construct_full_key(
                        perm, rtype, partial))
        return fulls

    def _key_permission(self, key):
        return key.split('#')[0].split('.')[0]

    def _key_rtype(self, key):
        return key.split('#')[0].split('.')[1]

    def _get_results_qs_for_serialization(self, key):
        return self.BASE_QUERYSETS[self._key_rtype(key)
        ].prefetch_related(
            'problem_instance__round',
        ).select_related(
            'problem_instance', 'problem_instance__contest',
        )
