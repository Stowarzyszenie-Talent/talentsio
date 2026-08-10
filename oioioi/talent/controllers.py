from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from oioioi.contests.models import Contest
from oioioi.contests.scores import IntegerScore
from oioioi.participants.controllers import ParticipantsController
from oioioi.phase.controllers import (
    PhaseMixinForContestController,
    PhaseRankingController,
)
from oioioi.programs.controllers import ProgrammingContestController
from oioioi.scoresreveal.utils import get_scores_reveal_config
from oioioi.talent.models import TalentRegistrationSwitch, TalentRegistration

def _phase_end_human():
    minutes = settings.TALENT_PHASE2_END.seconds // 60
    return f"{minutes // 60}:{minutes % 60}"


def _is_camp():
    cids = settings.TALENT_CONTEST_IDS
    if not cids:
        return False
    try:
        if TalentRegistrationSwitch.objects.all().exists():
            return True
        if len(Contest.objects.filter(id__in=cids)) != len(cids):
            return False
    except (OperationalError, ImproperlyConfigured, ProgrammingError):
        pass
    return not settings.TALENT_DISABLE_CAMP_INIT


class TalentOpenContestController(ProgrammingContestController):
    description = _("Talent open contest")
    # In migrations this isn't set correctly by the mixin
    is_phase_contest = True
    scoring_description = """Zasady oceniania:
        - Czas wykonania programu jest mierzony tak jak na Olimpiadzie Informatycznej, czyli liczy się liczba wykonanych instrukcji.
        - Od połowy limitu czasu punktacja testu spada liniowo do zera.
        - Punktacja grupy zależy od testu z minimalną punktacją.
        - Wynik za zadanie zależy od najlepszych (!) zgłoszeń w poszczególnych fazach.

        Fazy to podział na okresy czasowe z mnożnikami""" + (f""", obecnie:
        Kontest (x1) - po konteście do {_phase_end_human()} (x0.{settings.TALENT_SCORE1}) - od {_phase_end_human()} do początku ostatniego kontestu (x0.{settings.TALENT_SCORE2}){" - później (x0)" if settings.TALENT_BEZ_DOBIJANIA else ""}.""" if _is_camp() else ".") + """
        Mnożnik aplikuje się do różnicy punktów w aktualnej fazie względem maksimum z wcześniejszych faz, przy czym punktacja względem wcześniejszych faz nigdy nie maleje.
    """

    def ranking_controller(self):
        return TalentPhaseRankingController(self.contest)

    def order_submissions_qs(self, pi, qs):
        """TALENT FEATURE: abstract away picking either latest or best
        submissions for generating results.
        """
        #reveals_config = get_scores_reveal_config(pi)
        #if reveals_config is None or reveals_config.reveal_limit == 0:
        #    return qs.order_by('-date')
        return qs.order_by('-score', '-date')

    def fill_evaluation_environ(self, environ, submission):
        super(TalentOpenContestController, self).fill_evaluation_environ(
            environ, submission
        )

        environ['group_scorer'] = 'oioioi.programs.utils.min_group_scorer'
        environ['test_scorer'] = \
            'oioioi.programs.utils.threshold_linear_test_scorer'

TalentOpenContestController.mix_in(PhaseMixinForContestController)

class TalentContestController(TalentOpenContestController):
    description = _("Talent contest")

    def registration_controller(self):
        return ParticipantsController(self.contest)

class TalentPhaseRankingController(PhaseRankingController):
    RANKING_TYPES = PhaseRankingController.RANKING_TYPES.copy() + ['same_group_phased', 'same_group_clean']
    BASE_QUERYSETS = PhaseRankingController.BASE_QUERYSETS.copy()
    BASE_QUERYSETS['same_group_phased'] = BASE_QUERYSETS['default'].all()
    BASE_QUERYSETS['same_group_clean'] = BASE_QUERYSETS['clean'].all()
    TYPE_NAMES = PhaseRankingController.TYPE_NAMES.copy()
    TYPE_NAMES['same_group_phased'] = _("Default (group members only)")
    TYPE_NAMES['same_group_clean'] = _("Without multipliers (group members only)")

    def filter_users_for_ranking(self, key, queryset):
        queryset = super().filter_users_for_ranking(key, queryset)

        if self._key_rtype(key).startswith('same_group'):
            queryset = queryset.filter(
                talent_registration__contest=self.contest
            )

        return queryset

    def _always_included_user_ids(self):
        return set(
            TalentRegistration.objects.filter(contest=self.contest).values_list(
                'user_id', flat=True
            )
        )

    def _get_users_results(self, pis, results, rounds, users):
        by_user = defaultdict(dict)
        for r in results:
            by_user[r.user_id][r.problem_instance_id] = r
        included = set(by_user.keys()) | self._always_included_user_ids()
        users = users.filter(id__in=list(included))
        data = []
        all_rounds_trial = all(r.is_trial for r in rounds)
        users_without_submits = []
        for user in users.order_by('last_name', 'first_name', 'username'):
            by_user_row = by_user[user.id]
            user_results = []
            user_data = {'user': user, 'results': user_results, 'sum': None}

            for pi in pis:
                result = by_user_row.get(pi.id)
                if (
                    result
                    and hasattr(result, 'submission_report')
                    and hasattr(result.submission_report, 'submission_id')
                ):
                    submission_id = result.submission_report.submission_id
                    kwargs = {
                        'contest_id': self.contest.id,
                        'submission_id': submission_id,
                    }
                    result.url = reverse('submission', kwargs=kwargs)

                user_results.append(result)
                if (
                    result
                    and result.score
                    and (not pi.round.is_trial or all_rounds_trial)
                ):
                    if user_data['sum'] is None:
                        user_data['sum'] = result.score
                    else:
                        user_data['sum'] += result.score

            if user_data['sum'] is None:
                user_data['sum'] = IntegerScore(0)
                users_without_submits.append(user_data)
                continue

            if self._allow_zero_score() or user_data['sum'].to_int() != 0:
                data.append(user_data)

        for user_data in users_without_submits:
            data.append(user_data)

        return data
