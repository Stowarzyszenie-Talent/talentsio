from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError
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
    except (OperationalError, ImproperlyConfigured):
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
        - W zadaniach/kontestach bez odsłonięć wynik za zadanie zależy od ostatnich kompilujących się zgłoszeń w poszczególnych fazach, a tam, gdzie są odsłonięcia (np. w Grupie A), od najlepszych zgłoszeń w poszczególnych fazach.

        Fazy to podział na okresy czasowe z mnożnikami""" + (f""", obecnie:
        Kontest (x1) - po konteście do {_phase_end_human()} (x0.{settings.TALENT_SCORE1}) - od {_phase_end_human()} do początku ostatniego kontestu (x0.{settings.TALENT_SCORE2}){" - później (x0)" if settings.TALENT_BEZ_DOBIJANIA else ""}.""" if _is_camp() else ".") + """
        Mnożnik aplikuje się do różnicy punktów w aktualnej fazie względem maksimum z wcześniejszych faz, przy czym punktacja względem wcześniejszych faz nigdy nie maleje.
    """

    def ranking_controller(self):
        return PhaseRankingController(self.contest)

    def order_submissions_qs(self, pi, qs):
        """TALENT FEATURE: abstract away picking either latest or best
        submissions for generating results.
        """
        reveals_config = get_scores_reveal_config(pi)
        if reveals_config is None or reveals_config.reveal_limit == 0:
            return qs.order_by('-date')
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
