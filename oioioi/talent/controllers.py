from django.utils.translation import gettext_lazy as _

from oioioi.participants.controllers import ParticipantsController
from oioioi.phase.controllers import (
    PhaseMixinForContestController,
    PhaseRankingController,
)
from oioioi.programs.controllers import ProgrammingContestController
from oioioi.scoresreveal.utils import get_scores_reveal_config


class TalentOpenContestController(ProgrammingContestController):
    description = _("Talent open contest")
    # In migrations this isn't set correctly by the mixin
    is_phase_contest = True

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
