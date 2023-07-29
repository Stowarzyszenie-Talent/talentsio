from datetime import datetime, timezone  # pylint: disable=E0611

from django.urls import reverse

from oioioi.base.tests import TestCase, fake_time


class TestPerfdata(TestCase):
    fixtures = [
        'test_users',
        'test_contest',
        'test_full_package',
        'test_problem_instance',
        'test_submission_list',
    ]

    def get_submission_number(self):
        url = reverse('recent_submissions_number')
        return int(self.client.get(url).content)

    def test_perfdata(self):
        # The fixture's submissions are at 22:07:07 and 22:08.07
        # Just before second submission
        with fake_time(datetime(2012, 6, 3, 22, 8, 6, tzinfo=timezone.utc)):
            self.assertEqual(self.get_submission_number(), 1)
        # Just before first submission
        with fake_time(datetime(2012, 6, 3, 22, 7, 6, tzinfo=timezone.utc)):
            self.assertEqual(self.get_submission_number(), 0)
        # At second submission
        with fake_time(datetime(2012, 6, 3, 22, 8, 7, tzinfo=timezone.utc)):
            self.assertEqual(self.get_submission_number(), 1)
        # 1m1s after the second submission
        with fake_time(datetime(2012, 6, 3, 22, 9, 8, tzinfo=timezone.utc)):
            self.assertEqual(self.get_submission_number(), 0)
