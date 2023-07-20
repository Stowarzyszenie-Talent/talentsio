from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import override_settings
from django.urls import reverse

from oioioi.base.tests import TestCase
from oioioi.participants.models import Participant
from oioioi.supervision.models import Membership

class TestTalent(TestCase):

    def setUp(self):
        call_command('talent_camp_init')

    def register(self, username, group):
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

    def test_registration(self):
        self.register('a', 'a')
        self.register('d', 'd')
        self.register('e', 'e')
        self.assertEqual(User.objects.count(), 4)

        self.assertEqual(Participant.objects.count(), 2)
        pd = Participant.objects.get(user__username='d')
        pe = Participant.objects.get(user__username='e')
        self.assertEqual(pd.contest_id, 'd')
        self.assertEqual(pe.contest_id, 'e')

        self.assertEqual(Membership.objects.count(), 2)
        ma = Membership.objects.get(user__username='a')
        md = Membership.objects.get(user__username='d')
        self.assertEqual(ma.group.name, 'Grupa A')
        self.assertEqual(md.group.name, 'Grupa D')
