from datetime import datetime, timezone
from importlib import reload
from io import BytesIO
import os

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oioioi.base.tests import TestCase, fake_time
from oioioi.base.utils.pdf import extract_text_from_pdf
from oioioi.contests.current_contest import ContestMode
from oioioi.participants.models import Participant
from oioioi.phase.models import Phase
from oioioi.problems.models import (
    Problem,
    ProblemStatement,
)
from oioioi.supervision.models import Membership
from oioioi.talent.models import TalentRegistration, TalentRegistrationSwitch


def get_test_filename(name):
    return os.path.join(os.path.dirname(__file__), 'files', name)


class TestTalentProblemPackages(TestCase):
    fixtures = ['test_users', 'test_contest']

    def _check_talent_package(self, file, checkstr=None):
        file = get_test_filename(file)
        call_command("addproblem", file)
        statements = ProblemStatement.objects.filter()
        if checkstr is None:
            self.assertEqual(statements.count(), 0)
        else:
            self.assertEqual(statements.count(), 1)
            pdfcontent = extract_text_from_pdf(statements.get().content.file)
            self.assertTrue(checkstr in pdfcontent[0])
        Problem.objects.all().delete()

    def test_talent_package_compilation(self):
        self._check_talent_package("no_doc.zip", None)
        self._check_talent_package("pdf_tex_outdated.zip", b"ZMODYFIKOWANE")
        self._check_talent_package("pdf_tex_outdated.tar.gz", b"ZMODYFIKOWANE")
        for f in (
            "pdf.zip", "tex.zip", "pdf_tex_outdated_notalent.zip",
            "pdf_tex_current.zip", "pdf_tex_current.tar.gz",
        ):
            self._check_talent_package(f, b"Lorem ipsus")


@override_settings(CONTEST_MODE=ContestMode.neutral)
class TestTalent(TestCase):

    def setUp(self):
        call_command('talent_camp_init')

    def test_site_data(self):
        s = Site.objects.get(id=1)
        self.assertEqual(s.domain, 'oboz.talent.edu.pl')
        self.assertEqual(s.name, 'OIOIOI')

    def register(self, username, group, room='Rodzinny', should_fail=False):
        count = User.objects.count()
        response = self.client.post(reverse('sign-up'), {
            'username': username,
            'first_name': 'test',
            'last_name': 'user',
            'email': 'a@a.pl',
            'password1': 'a',
            'password2': 'a',
            'group': group,
            'room': room,
            'preferred_language': '',
            'terms_accepted': 'on',
            'captcha_0': 'bajo_jajo',
            # This and CAPTCHA_TEST_MODE is required
            'captcha_1': 'PASSED',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        if should_fail:
            self.assertNotContains(response, "Sign-up successful")
            self.assertEqual(count, User.objects.count())
            self.assertEqual(TalentRegistration.objects.filter(
                user__username=username,
            ).count(), 0)
        else:
            self.assertContains(response, "Sign-up successful")
            self.assertEqual(count+1, User.objects.count())
            if group != 'brak':
                tr = TalentRegistration.objects.get(user__username=username)
                self.assertEqual(tr.contest_id, group)
                self.assertEqual(tr.room, room)
            else:
                self.assertEqual(TalentRegistration.objects.filter(
                    user__username=username,
                ).count(), 0)

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
        self.del_user()

        for r in ['0', '011', '1111', 'amogus', '']:
            self.register('a', 'e', r, True)
            self.register('a', 'brak', r, True)

        for r in ['1', '10', '999', 'Rodzinny']:
            self.register('a', 'e', r)
            self.del_user()
            self.register('a', 'brak', r)
            self.del_user()

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

    def test_attendance_list(self):
        self.register('a', 'a', room='69')
        self.assertTrue(self.client.login(username="admin"))
        url = self.tr_admin_url('a')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Make attendance list")

        att_list_url = reverse(
            'talent_att_list_gen_view',
            kwargs={'contest_id': 'a',},
        )
        resp = self.client.post(att_list_url, data={'date': "2024-02-01"})
        self.assertEqual(resp.status_code, 200)
        pdf_data = BytesIO(b"".join(resp.streaming_content))
        pdf_text = extract_text_from_pdf(pdf_data)[0].decode('utf-8')
        for s in ['Grupa A - 01.02.2024', '1.', 'user', 'test', '69']:
            self.assertIn(s, pdf_text)

        def get_time(days=0, hours=0, minutes=0):
            return datetime(2012, 1, 1+days, hours, minutes, tzinfo=timezone.utc)

        for time, date in [
            (get_time(), get_time(1)),
            (get_time(1), get_time(1)),
            (get_time(1, 10), get_time(1)),
            (get_time(1, 14), get_time(1)),
            (get_time(1, 14, 6), get_time(2)),
            (get_time(1, 17), get_time(2)),
            (get_time(4, 14), get_time(4)),
            # When there is no future/ongoing contest day, `today` is expected.
            (get_time(4, 14, 6), get_time(4)),
            (get_time(4, 17), get_time(4)),
        ]:
            with fake_time(time):
                resp = self.client.get(att_list_url)
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, date.strftime('%Y-%m-%d'))

    def _change_room_number(self, value, should_fail=False):
        prev_value = TalentRegistration.objects.get(user__username="a").room
        assert prev_value != value or should_fail
        url = reverse('talent_camp_data', kwargs={'contest_id': 'a'})
        resp = self.client.post(url, data={'room': value}, follow=True)
        self.assertContains(resp, "Room number (e.g.")
        new_value = TalentRegistration.objects.get(user__username="a").room
        if not should_fail:
            self.assertEqual(new_value, value)
            self.assertContains(resp, "Successfully changed!")
            self.assertContains(resp, value)
            self.assertNotContains(resp, "Nothing has been changed.")
            self.assertNotContains(resp, "This field is required")
            self.assertNotContains(resp, "Enter a valid value.")
        else:
            self.assertEqual(new_value, prev_value)
            if prev_value == value:
                self.assertContains(resp, "Nothing has been changed.")
            elif len(value) == 0:
                self.assertContains(resp, "This field is required")
            else:
                self.assertContains(resp, "Enter a valid value.")
            self.assertNotContains(resp, "Successfully changed!")

    def test_camp_data(self):
        url = reverse('talent_camp_data', kwargs={'contest_id': 'a'})
        resp = self.client.get(url, follow=True)
        self.assertContains(resp, "Log in")

        self.assertTrue(self.client.login(username="admin"))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        self.client.logout()
        self.register('a', 'a', room='69')
        self.assertTrue(self.client.login(username="a"))
        resp = self.client.get(reverse('index'))
        self.assertContains(resp, "My camp data") # In account menu

        resp = self.client.get(url)
        self.assertContains(resp, "Camp data")
        self.assertRegex(
            resp.content.decode('utf-8').replace('\n', ''),
            r'Current contest group: *<a href="?/c/a/"?>Grupa A</a>',
        )
        self.assertContains(resp, _("room_number_desc"))
        self.assertContains(resp, "69")

        self._change_room_number('69', True)
        self._change_room_number('', True)
        self._change_room_number('01', True)
        self._change_room_number('1')
        self._change_room_number('301')
        self._change_room_number('Rodzinny')
        self._change_room_number('69')

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
        self.assertEqual(count, Phase.objects.count())
        self.assertEqual(Phase.objects.filter(multiplier=69).count(), 0)

    def test_contest_rules(self):
        import oioioi.talent.controllers
        reload(oioioi.talent.controllers)
        url = reverse('contest_rules', kwargs={'contest_id': 'a'})
        self.assertTrue(self.client.login(username="admin"))
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "21:30")
        self.assertContains(response, "x0.75")
        self.assertContains(response, "x0.60")

    @override_settings(TALENT_DISABLE_CAMP_INIT=True)
    def test_contest_rules_not_camp(self):
        import oioioi.talent.controllers
        reload(oioioi.talent.controllers)
        url = reverse('contest_rules', kwargs={'contest_id': 'a'})
        self.assertTrue(self.client.login(username="admin"))
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "21:30")
        self.assertContains(response, "x0.75")
        self.assertContains(response, "x0.60")
        TalentRegistrationSwitch.objects.all().delete()
        reload(oioioi.talent.controllers)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "21:30")
        self.assertNotContains(response, "x0.75")
        self.assertNotContains(response, "x0.60")
