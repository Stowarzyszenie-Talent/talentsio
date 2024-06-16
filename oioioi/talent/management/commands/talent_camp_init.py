from datetime import timedelta, datetime
from getpass import getpass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware
from django.utils.translation import gettext as _
from oioioi.contests.models import Contest, Round
from oioioi.dashboard.models import DashboardMessage
from oioioi.phase.models import Phase
from oioioi.questions.models import MessageNotifierConfig
from oioioi.scoresreveal.models import ScoreRevealContestConfig
from oioioi.supervision.models import Supervision, Group
from oioioi.talent.models import TalentRegistrationSwitch


OPEN_CONTEST = "oioioi.talent.controllers.TalentOpenContestController"
CLOSED_CONTEST = "oioioi.talent.controllers.TalentContestController"
User = get_user_model()


def createsuperuser(username, password, email, first_name, last_name):
    if User.objects.filter(username=username).exists():
        print("User {} already exists!".format(username))
        return
    if len(password)<1:
        password = getpass("Password for {}: ".format(username))
        password2 = getpass("Password for {} (again): ".format(username))
        while password!=password2 or len(password)<1:
            print("The passwords don't match! Try again.")
            password = getpass("Password for {}: ".format(username))
            password2 = getpass("Password for {} (again): ".format(username))
    User.objects.create_superuser(
        username,
        email,
        password,
        first_name=first_name,
        last_name=last_name,
    )


def mkphase(r, mul, start_date):
    Phase.objects.update_or_create(
        round=r,
        multiplier=mul,
        defaults={'start_date': start_date,},
    )


def day(round):
    return round.start_date - settings.TALENT_CONTEST_START[round.contest_id]


class Command(BaseCommand):
    help = _(
        "Create contests, rounds, etc. for Stowarzyszenie Talent's camps"
    )

    def handle(self, *args, **options):

        assert not settings.TALENT_DISABLE_CAMP_INIT

        with transaction.atomic():
            score1 = settings.TALENT_SCORE1
            score2 = settings.TALENT_SCORE2
            if Phase.objects.exclude(multiplier__in=(score1, score2, 0)):
                print("Phase multipliers have been changed!\n"
                      "You need to delete old phases, "
                      "run this again and run update_scores.\n"
                      "Aborting.")
                return

            print("--- Creating default superusers")
            for tup in settings.TALENT_DEFAULT_SUPERUSERS:
                createsuperuser(*tup)

            today = make_aware(datetime.strptime(
                settings.TALENT_CAMP_START_DATE,
                "%d.%m.%Y",
            ))
            contest_names = settings.TALENT_CONTEST_NAMES
            contest_days = settings.TALENT_CONTEST_DAYS

            print("--- Creating contests, rounds, etc.")
            # Contests
            for i in settings.TALENT_CONTEST_IDS:
                controller = CLOSED_CONTEST
                contest, _ = Contest.objects.get_or_create(
                    id=i,
                    name=contest_names[i],
                    controller_name=controller,
                )
                # Rounds
                for roundnum, daynum in contest_days:
                    cday = today + timedelta(days=daynum)
                    name = "Dzień " + str(roundnum)
                    round_start = cday + settings.TALENT_CONTEST_START[i]
                    round_results = cday + settings.TALENT_CONTEST_RESULTS[i]
                    Round.objects.update_or_create(
                        contest=contest,
                        name=name,
                        defaults={
                            "start_date": round_start,
                            "results_date": round_results,
                        }
                    )

            # Trial contest & round. We do not update the values so as not to
            # overwrite manual and temporary changes.
            contest, _ = Contest.objects.get_or_create(
                id="p",
                name="Kontest próbny",
                controller_name=OPEN_CONTEST,
            )
            Round.objects.get_or_create(
                contest=contest,
                name="Runda próbna",
                defaults={
                    "start_date": today,
                    "results_date": today,
                }
            )
            DashboardMessage.objects.get_or_create(
                contest=contest,
                defaults={
                    "content": settings.TALENT_DASHBOARD_MESSAGE,
                }
            )

            # Supervision groups
            for i in settings.TALENT_SUPERVISED_IDS:
                group, _ = Group.objects.get_or_create(name=contest_names[i])
                # Supervisions
                for r in Round.objects.filter(contest_id=i):
                    Supervision.objects.update_or_create(
                        group=group,
                        round=r,
                        defaults={
                            "start_date": r.start_date,
                            "end_date": day(r) + settings.TALENT_CONTEST_END[i],
                        }
                    )

            # Phases
            final_roundnum = len(contest_days)
            finday = today + timedelta(days=contest_days[-1][1])
            for r in Round.objects.filter(
                contest_id__in=settings.TALENT_PHASED_IDS,
            ):
                rdate = day(r)
                contest_start = settings.TALENT_CONTEST_START[r.contest_id]
                contest_end = settings.TALENT_CONTEST_END[r.contest_id]
                # Fazy z mnoznikiem 0 około ostatnich kontestów
                if settings.TALENT_BEZ_DOBIJANIA:
                    if str(final_roundnum) in r.name:
                        mkphase(r, 0, rdate + contest_end)
                        continue
                    mkphase(r, 0, finday + contest_start)
                # Pozostale fazy
                for mul, delta in (
                    (score1, contest_end,),
                    (score2, settings.TALENT_PHASE2_END,)
                ):
                    mkphase(r, mul, rdate + delta)

            # Default score reveal configs
            for cid, limit in settings.TALENT_DEFAULT_SCOREREVEALS.items():
                ScoreRevealContestConfig.objects.update_or_create(
                    contest=Contest.objects.get(id=cid),
                    defaults={
                        "reveal_limit": limit,
                    }
                )

            # Notified-about-new-questions configs
            for login, contestids in settings.TALENT_MAIL_NOTIFICATIONS.items():
                user = User.objects.get(username=login)
                for cid in contestids:
                    MessageNotifierConfig.objects.get_or_create(
                        contest_id=cid,
                        user=user,
                    )

            # Enable talent registration (automatic assigning to groups)
            TalentRegistrationSwitch.objects.get_or_create(status=True)

            # Set the site domain and name for urls in password reset emails.
            s = Site.objects.get(id=settings.SITE_ID)
            s.domain = settings.SITE_DOMAIN
            s.name = settings.SITE_NAME
            s.save()

        print("--- Finished!")
