# pylint: disable=wildcard-import
import django

from oioioi.default_settings import *

TIME_ZONE = 'UTC'

SITE_ID = 1

ADMINS = (('Test admin', 'admin@example.com'),)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

# Enable optional modules.
INSTALLED_APPS = (
    'oioioi.talent',
    'oioioi.phase',
    'oioioi.supervision',
    'oioioi.contestlogo',
    'oioioi.teachers',
    'oioioi.ipdnsauth',
    'oioioi.participants',
    'oioioi.oi',
    'oioioi.printing',
    'oioioi.zeus',
    'oioioi.testrun',
    'oioioi.scoresreveal',
    'oioioi.oireports',
    'oioioi.oisubmit',
    'oioioi.szkopul',
    'oioioi.complaints',
    'oioioi.contestexcl',
    'oioioi.forum',
    'oioioi.exportszu',
    'oioioi.plagiarism',
    'oioioi.similarsubmits',
    'oioioi.disqualification',
    'oioioi.confirmations',
    'oioioi.ctimes',
    'oioioi.acm',
    'oioioi.suspendjudge',
    'oioioi.submitservice',
    'oioioi.timeline',
    'oioioi.statistics',
    'oioioi.amppz',
    'oioioi.balloons',
    'oioioi.publicsolutions',
    'oioioi.testspackages',
    'oioioi.teams',
    'oioioi.pa',
    'oioioi.notifications',
    'oioioi.mailsubmit',
    'oioioi.globalmessage',
    'oioioi.portals',
    'oioioi.newsfeed',
    'oioioi.simpleui',
    'oioioi.livedata',
    'oioioi.usergroups',
    'oioioi.problemsharing',
    'oioioi.usercontests',
    'oioioi.mp',
) + INSTALLED_APPS

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'oioioi.contestlogo.processors.logo_processor',
    'oioioi.contestlogo.processors.icon_processor',
    'oioioi.supervision.processors.supervision_processor',
    'oioioi.globalmessage.processors.global_message_processor',
    'oioioi.phase.processors.phase_processor',
    'oioioi.portals.processors.portal_processor',
]

AUTHENTICATION_BACKENDS += (
    'oioioi.base.tests.IgnorePasswordAuthBackend',
    'oioioi.teachers.auth.TeacherAuthBackend',
    'oioioi.usercontests.auth.UserContestAuthBackend',
)

MIDDLEWARE += (
    'oioioi.base.tests.FakeTimeMiddleware',
)

TESTS = True
CAPTCHA_TEST_MODE = True
MOCK_RANKINGSD = True

SECRET_KEY = 'no_secret'
OISUBMIT_MAGICKEY = 'abcdef'
COMPRESS_ENABLED = False
COMPRESS_PRECOMPILERS = ()
CELERY_ALWAYS_EAGER = True
SIOWORKERS_BACKEND = 'oioioi.sioworkers.backends.LocalBackend'
FILETRACKER_CLIENT_FACTORY = 'filetracker.client.dummy.DummyClient'
FILETRACKER_URL = None
USE_UNSAFE_EXEC = True
USE_UNSAFE_CHECKER = True

AVAILABLE_COMPILERS = SYSTEM_COMPILERS
DEFAULT_COMPILERS = SYSTEM_DEFAULT_COMPILERS

USE_SINOLPACK_MAKEFILES = True
SINOLPACK_RESTRICT_HTML = False


COMPLAINTS_EMAIL = 'dummy@example.com'
COMPLAINTS_SUBJECT_PREFIX = '[oioioi-complaints] '

WARN_ABOUT_REPEATED_SUBMISSION = False

# Experimental according to default_settings.py
USE_ACE_EDITOR = True

PROBLEM_SOURCES += ('oioioi.zeus.problem_sources.ZeusProblemSource',)

ZEUS_INSTANCES = {
    'dummy': ('__use_object__', 'oioioi.zeus.tests.ZeusDummyServer', ('', '', '')),
}

# dummy.DummyCache ...?
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

CONFIG_VERSION = INSTALLATION_CONFIG_VERSION

STATIC_ROOT = ''

# Do not print migrations DEBUG to console.
LOGGING['loggers']['django.db.backends.schema'] = {
    'handlers': ['console'],
    'level': 'INFO',
}

# Settings for initialiasing OIOIOI at the start of a Stowarzyszenie Talent's
# camp by the 'talent_camp_init' command in oioioi.talent
from datetime import timedelta, datetime

# The day of the trial contest as "%d.%m.%Y"
TALENT_CAMP_START_DATE = datetime.strftime(datetime.today(), "%d.%m.%Y")

# (username, password ("" to prompt), email ("" is ok), first_name, last_name)
TALENT_DEFAULT_SUPERUSERS = [
    ("admin", "admin", "admin@admin.pl", "admin", "admin"),
]

TALENT_SCORE1 = 75
TALENT_PHASE2_END = timedelta(hours=21, minutes=30)
TALENT_SCORE2 = 60

TALENT_CONTEST_IDS = ["e", "d", "a",]
# The rest will be open
TALENT_CLOSED_CONTEST_IDS = ["e", "d",]
# Groups for which to setup supervision
TALENT_SUPERVISED_IDS = ["a", "d",]
# Groups for which to create phases
TALENT_PHASED_IDS = ["a",]
# Default amount of score reveals for contests
TALENT_DEFAULT_SCOREREVEALS = {
    "a": 15,
}
TALENT_MAIL_NOTIFICATIONS = {
    "admin": ["a",],
}

TALENT_CONTEST_NAMES = {
    "a": "Grupa A",
    "d": "Grupa D",
    "e": "Grupa E",
}
# For registration
TALENT_GROUP_FORM_CHOICES = [("", "")] + \
    list(TALENT_CONTEST_NAMES.items()) + \
    [("brak", "Brak grupy (Trzeba mieć grupę! Wybieram na własne ryzyko)"),]

# (number of round, number of days from the start of the camp)
TALENT_CONTEST_DAYS = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
)
TALENT_CONTEST_START = {
    "a": timedelta(hours=9),
    "d": timedelta(hours=9, minutes=30),
    "e": timedelta(hours=9, minutes=30),
}
TALENT_CONTEST_END = {
    "a": timedelta(hours=14),
    "d": timedelta(hours=12, minutes=30),
    "e": timedelta(hours=12, minutes=30),
}
TALENT_CONTEST_RESULTS = {
    "a": timedelta(hours=14, minutes=5),
    "d": timedelta(hours=14, minutes=5),
    "e": timedelta(hours=14, minutes=5),
}
TALENT_DASHBOARD_MESSAGE = "Example dashboard message"
