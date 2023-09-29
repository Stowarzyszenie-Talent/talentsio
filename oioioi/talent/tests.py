from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import override_settings
from django.urls import reverse

from oioioi.base.tests import TestCase
from oioioi.contests.current_contest import ContestMode
from oioioi.participants.models import Participant
from oioioi.phase.models import Phase
from oioioi.supervision.models import Membership
from oioioi.talent.models import TalentRegistration

@override_settings(CONTEST_MODE=ContestMode.neutral)
class TestTalent(TestCase):

    def setUp(self):
        call_command('talent_camp_init')

    def register(self, username, group):
        count = User.objects.count()
        response = self.client.post(reverse('sign-up'), {
            'username': username,
            'first_name': 'test',
            'last_name': 'user',
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
        self.assertContains(response, "Sign-up successful")
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

    def assertMemberships(self, *args):
        self.assertEqual(len(args), Membership.objects.count())
        for i in args:
            self.assertTrue(Membership.objects.filter(group__name="Grupa " + i.upper()))

    def del_user(self):
        User.objects.filter(username='a').delete()

    # ids: e,d,a; closed: e,d; supervised: a,d; phased: a
    def test_registrations(self):
        self.register('a', 'a')
        self.assertMemberships('a')
        self.assertParticipants('a')
        self.del_user()

        self.register('a', 'd')
        self.assertMemberships('d')
        self.assertParticipants('a', 'd')
        self.del_user()

        self.register('a', 'e')
        self.assertMemberships()
        self.assertParticipants('a', 'e')
        self.del_user()

        self.register('a', 'brak')
        self.assertMemberships()
        # This was changed, ungrouped people shouldn't see semi-closed contests
        self.assertParticipants() #('a')
        self.assertEqual(TalentRegistration.objects.count(), 0)

    def tr_admin_url(self, id):
        return reverse(
            'oioioiadmin:talent_talentregistration_changelist',
            kwargs={'contest_id': id,},
        )

    def move(self, group):
        self.assertTrue(self.client.login(username="admin"))
        u = User.objects.get(username='a')
        url = self.tr_admin_url(TalentRegistration.objects.get().contest_id)
        resp = self.client.get(url)

        self.assertContains(resp, "test user")
        data = {
            'action': 'move_to_' + group,
            'select_across': 1,
            '_selected_action': u.id,
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Success!")
        self.assertEqual(TalentRegistration.objects.count(), 1)
        self.assertEqual(TalentRegistration.objects.get().contest_id, group)
        self.client.logout()

    def test_moving_panel(self):
        self.register('a', 'a')
        self.assertTrue(self.client.login(username="admin"))
        url = self.tr_admin_url('a')
        resp = self.client.get(url)
        self.assertContains(resp, "test user")
        for i in ('d', 'e'):
            resp = self.client.get(self.tr_admin_url(i))
            self.assertNotContains(resp, "test user")

    def test_moving(self):
        self.register('a', 'a')
        self.move('e')
        self.assertMemberships()
        self.assertParticipants('a', 'e')
        self.move('d')
        self.assertMemberships('d')
        self.assertParticipants('a', 'd', 'e')
        self.move('a')
        self.assertMemberships('a')
        self.assertParticipants('a', 'd', 'e')
        self.del_user()

        self.register('a', 'e')
        self.move('a')
        self.assertMemberships('a')
        self.assertParticipants('a', 'e')

    @override_settings(TALENT_SCORE1=69)
    def test_changing_multipliers(self):
        count = Phase.objects.count()
        call_command('talent_camp_init')
        self.assertEqual(count, Phase.objects.count())
        self.assertEqual(Phase.objects.filter(multiplier=69).count(), 0)
