from django.db import models
from django.utils.translation import ugettext_lazy as _

from oioioi.contests.models import Round


class Phase(models.Model):
    round = models.ForeignKey(Round, verbose_name=_("round"))
    start_date = models.DateTimeField(verbose_name=_("start date"))
    multiplier = models.IntegerField(verbose_name=_("phase multiplier"))

    class Meta(object):
        verbose_name = _("phase")
        verbose_name_plural = _("phases")
        ordering = ['start_date']
