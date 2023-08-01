from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import override_settings

from oioioi.base.tests import TestCase
from oioioi.participants.models import Participant
from oioioi.phase.models import Phase
from oioioi.supervision.models import Membership
from oioioi.talent.models import TalentRegistration

class TestTalent(TestCase):

    def setUp(self):
        call_command('talent_camp_init')

    def register(self, username, group):
        count = User.objects.count()
        response = self.client.post('/register/', {
            'username': username,
            'first_name': 'a',
            'last_name': 'a',
            'email': 'a@a.pl',
            'password1': 'a',
            'password2': 'a',
            'group': group,
            'preferred_language': '',
            'terms_accepted': 'on',
            'captcha_0': 'bajo_jajo',
            # This and CAPTCHA_TEST_MODE is required
            'captcha_1': 'PASSED',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        print(response.content)
        self.assertContains(response, "Registration successful")
        self.assertEqual(count+1, User.objects.count())
        if group != 'brak':
            self.assertEqual(TalentRegistration.objects.get(
                user__username=username,
            ).contest_id, group)
        else:
            self.assertEqual(TalentRegistration.objects.filter(
                user__username=username,
            ).count(), 0)
        self.assertEqual(count+1, User.objects.count())

    def assertParticipants(self, *args):
        self.assertEqual(len(args), Participant.objects.count())
        for i in args:
            self.assertTrue(Participant.objects.filter(contest_id=i))

    def test_registrations(self):
        self.register('a', 'a')
        m = Membership.objects.get()
        self.assertEqual(m.group.name, 'Grupa A')
        self.assertParticipants('a')
        User.objects.filter(username='a').delete()

        self.register('a', 'd')
        m = Membership.objects.get()
        self.assertEqual(m.group.name, 'Grupa D')
        self.assertParticipants('a', 'd')
        User.objects.filter(username='a').delete()

        self.register('a', 'e')
        self.assertEqual(Membership.objects.count(), 0)
        self.assertParticipants('a', 'e')
        User.objects.filter(username='a').delete()

        self.register('a', 'brak')
        self.assertEqual(Membership.objects.count(), 0)
        self.assertParticipants('a')

    @override_settings(TALENT_SCORE1=69)
    def test_changing_multipliers(self):
        count = Phase.objects.count()
        call_command('talent_camp_init')
        self.assertEqual(count, Phase.objects.count())
        self.assertEqual(Phase.objects.filter(multiplier=69).count(), 0)
