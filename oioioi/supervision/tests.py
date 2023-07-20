from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.urls import reverse

from oioioi.base.tests import TestCase
from oioioi.contests.current_contest import ContestMode
from oioioi.contests.models import Round
from oioioi.supervision.models import Membership

class TestSupervision(TestCase):
    fixtures = [
        'test_contest',
        'test_extra_contests',
        'test_supervision',
        'test_users',
    ]

    def see_contests(self, ids, not_ids=[]):
        response = self.client.get(reverse('select_contest'))
        self.assertEqual(response.status_code, 200)
        for i in ids:
            self.assertContains(response, i)
        for i in not_ids:
            self.assertNotContains(response, i)

    def see_rounds(self, rounds, not_rounds=[]):
        for r in rounds:
            url = reverse(
                'contest_messages',
                kwargs={'contest_id': r.contest_id,},
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, r.name)

        for r in not_rounds:
            url = reverse(
                'contest_messages',
                kwargs={'contest_id': r.contest_id,},
            )
            response = self.client.get(url)
            if response.status_code == 200:
                self.assertNotContains(response, r.name)

    @override_settings(CONTEST_MODE=ContestMode.neutral)
    def test_supervision(self):
        self.assertTrue(self.client.login(username='test_user'))
        user = User.objects.get(username='test_user')
        r1 = Round.objects.get(id=1)
        r3 = Round.objects.get(id=3)
        r4 = Round.objects.create(
            id=4,
            name="Round 4",
            contest=r3.contest,
            start_date=r3.start_date,
            end_date=r3.end_date,
            results_date=r3.results_date,
        ) # Not covered by a supervision
        m1 = Membership.objects.create(user=user, group_id=1, is_present=False)
        Membership.objects.create(user=user, group_id=2) # Past supervision

        response = self.client.get(reverse('select_contest'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "supervision-badge")
        self.see_contests(['c', 'c1', 'c2'])
        self.see_rounds([r4], [r1, r3])

        m1.is_present = True
        m1.save()

        response = self.client.get(reverse('select_contest'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "supervision-badge")
        self.see_contests(['c', 'c2'], ['c1'])
        self.see_rounds([r1, r3], [r4])

        # Anonymous users caused problems in the past
        self.client.logout()
        response = self.client.get(reverse('select_contest'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "supervision-badge")
        self.see_contests(['c', 'c1', 'c2'])
        self.see_rounds([r4], [r1, r3])
