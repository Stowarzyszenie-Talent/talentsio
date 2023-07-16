from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from oioioi.contests.fields import ScoreField
from oioioi.contests.models import ProblemInstance, Round


class Phase(models.Model):
    round = models.ForeignKey(Round, verbose_name=_("round"), on_delete=models.CASCADE)
    start_date = models.DateTimeField(verbose_name=_("start date"))
    multiplier = models.IntegerField(verbose_name=_("phase multiplier"))

    class Meta(object):
        verbose_name = _("phase")
        verbose_name_plural = _("phases")
        ordering = ['start_date']

    def __str__(self):
        return str(
            "{} x{} {} {}".format(_("phase"), self.multiplier, _("inside"), self.round)
        )


# These are only for rankings and the submission_report field is "optional"
class UserCleanResultForProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem_instance = models.ForeignKey(ProblemInstance, on_delete=models.CASCADE)
    score = ScoreField(blank=True, null=True)

    class Meta(object):
        unique_together = ('user', 'problem_instance')


class UserFirstPhaseResultForProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem_instance = models.ForeignKey(ProblemInstance, on_delete=models.CASCADE)
    score = ScoreField(blank=True, null=True)

    class Meta(object):
        unique_together = ('user', 'problem_instance')
