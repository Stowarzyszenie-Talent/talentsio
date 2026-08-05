from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

from oioioi.contests.models import Contest
from oioioi.participants.controllers import ParticipantsController
from oioioi.phase.controllers import (
    PhaseMixinForContestController,
    PhaseRankingController,
)
from oioioi.programs.controllers import ProgrammingContestController
from oioioi.scoresreveal.utils import get_scores_reveal_config
from oioioi.talent.models import TalentRegistrationSwitch

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
