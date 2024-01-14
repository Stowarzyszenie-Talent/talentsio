import os

from datetime import datetime, timezone  # pylint: disable=E0611

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import override_settings
from django.urls import reverse

from oioioi.base.tests import TestCase, fake_time
from oioioi.contests.models import (
    Contest,
    Submission,
    Round,
)
from oioioi.problems.models import Problem
from oioioi.problems.utils import get_new_problem_instance
from oioioi.rankings.controllers import CONTEST_RANKING_KEY
from oioioi.talent.management.commands.talent_camp_init import OPEN_CONTEST

@override_settings(TALENT_CAMP_START_DATE="1.1.2012")
class TestTalent(TestCase):
    fixtures = ['test_users',] # 'test_contest']

    def get_test_filename(self, name):
        return os.path.join(self.base_dir, name)

    def setUp(self):
        call_command('talent_camp_init')
        self.base_dir = os.path.join(os.path.dirname(__file__), 'files')
        self.contest = Contest.objects.get(id='a')
        # We ought to test anonymous users too
        self.contest.controller_name = OPEN_CONTEST
        self.contest.save()
        self.c_kwargs = {'contest_id': self.contest.id}
        call_command('addproblem', self.get_test_filename('grupy.zip'))
        self.pi = get_new_problem_instance(Problem.objects.get(), self.contest)
        self.pi.round = Round.objects.filter(contest_id=self.contest.id).first()
        self.pi.save()

    # from baloons.tests
    def _submit_solution(self, user, source_file):
        url = reverse('submit', kwargs=self.c_kwargs)
        data = {
            'problem_instance_id': self.pi.id,
            'file': open(self.get_test_filename(source_file), 'rb'),
            'user': user.username,
            'kind': 'NORMAL',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        return response

    def switch_ranking_mode(self, rtype):
        url = reverse(
            'change_phase_ranking_type',
            kwargs=self.c_kwargs | {
                'key': CONTEST_RANKING_KEY,
                'rtype': rtype,
            },
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def check_score(self, score):
        url = reverse('default_ranking', kwargs=self.c_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # This pattern occurs in the Sum column
        self.assertContains(response, '>{}<'.format(str(score)), 1)

    def check_modes(self):
        self.check_score(77)
        self.switch_ranking_mode('first')
        self.check_score(20)
        self.switch_ranking_mode('clean')
        self.check_score(100)
        self.switch_ranking_mode('default')
        self.check_score(77)

    def test_phases(self):
        self.assertTrue(self.client.login(username='test_admin'))
        user = User.objects.get(username='test_user')

        # In first phase
        with fake_time(datetime(2012, 1, 2, 10, 0, tzinfo=timezone.utc)):
            self._submit_solution(user, 'grupy-20.cpp')
        # In second phase
        with fake_time(datetime(2012, 1, 2, 15, 0, tzinfo=timezone.utc)):
            self._submit_solution(user, 'grupy-80.cpp')
        # In third phase
        with fake_time(datetime(2012, 1, 2, 23, 0, tzinfo=timezone.utc)):
            self._submit_solution(user, 'grupy-100.cpp')
        self.assertEqual(Submission.objects.count(), 3)
        # Sanity check
        response = self.client.get(reverse(
            'submission',
            kwargs=self.c_kwargs | {'submission_id': '1'},
        ))
        self.assertContains(response, '>20<')

        self.check_modes()
        self.client.logout()
        self.check_modes()
        self.assertTrue(self.client.login(username='test_user'))
        self.check_modes()

        problems_url = reverse('problems_list', kwargs=self.c_kwargs)
        response = self.client.get(problems_url)
        self.assertContains(response, '> 100<')

        self.assertTrue(self.client.login(username='test_admin'))
        response = self.client.post(
            reverse('oioioiadmin:contests_submission_changelist'),
            {
                'action': 'delete_selected',
                '_selected_action': ['3'], # The 100 submission.
                'post': 'yes',
            }
        )
        self.assertEqual(Submission.objects.count(), 2)

        self.assertTrue(self.client.login(username='test_user'))
        self.switch_ranking_mode('clean')
        self.check_score(80)
        response = self.client.get(problems_url)
        self.assertContains(response, '> 80<')
