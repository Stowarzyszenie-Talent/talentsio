from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from oioioi.base.utils.deps import check_django_app_dependencies
from oioioi.contests.models import Contest


check_django_app_dependencies(__name__, ['oioioi.phase'])
check_django_app_dependencies(__name__, ['oioioi.supervision'])
check_django_app_dependencies(__name__, ['oioioi.scoresreveal'])

class TalentRegistrationSwitch(models.Model):
    status = models.BooleanField(default=True, verbose_name=_("status"))

class TalentRegistration(models.Model):
    user = models.OneToOneField(
        User,
        related_name="talent_registration",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    contest = models.ForeignKey(
        Contest,
        verbose_name=_("contest"),
        on_delete=models.CASCADE,
    )
    room = models.CharField(
        max_length=15,
        verbose_name=_("room_number_short_desc"),
        null=True,
    )

    class Meta(object):
        verbose_name = _("Talent registration")
        verbose_name_plural = _("Talent registrations")
        ordering = ['user__last_name']
    
    def __str__(self):
        return str("{} {} {}".format(self.user, _("inside"), self.contest))

class TalentParentContest(models.Model):
    contest = models.OneToOneField(
        Contest,
        verbose_name=_("contest"),
        related_name='talent_parent_contest',
        on_delete=models.CASCADE,
    )
    parent_contest = models.ForeignKey(
        Contest,
        verbose_name=_("parent contest"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    class Meta(object):
        verbose_name = _("Parent contest")
