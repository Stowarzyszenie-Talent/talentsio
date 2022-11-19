from django.test.utils import override_settings
from django.urls import reverse

from oioioi.base.tests import TestCase
from oioioi.contests.models import Contest


class TestDashboardMessage(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_templates']

    def test_adding_message(self):
        # Add a dashboard message
        self.assertTrue(self.client.login(username='test_admin'))
        contest = Contest.objects.get()
        url = reverse('dashboard_message_edit', kwargs={'contest_id': contest.id})
        post_data = {
            'content': 'Test dashboard message',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        # Check if message is visible
        self.assertTrue(self.client.login(username='test_user2'))
        url = reverse('contest_dashboard', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertContains(response, 'Test dashboard message')


class TestMessagesSection(TestCase):
    fixtures = [
        'test_users',
        'test_contest',
        'test_full_package',
        'test_problem_instance',
        'test_messages',
    ]

    @override_settings(NUM_DASHBOARD_MESSAGES=6)
    def test_show_more_button_visible(self):
        self.assertTrue(self.client.login(username='test_user'))
        contest = Contest.objects.get()
        url = reverse('contest_dashboard', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Show more')

    @override_settings(NUM_DASHBOARD_MESSAGES=7)
    def test_show_more_button_not_visible(self):
        self.assertTrue(self.client.login(username='test_user'))
        contest = Contest.objects.get()
        url = reverse('contest_dashboard', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Show more')

    def test_show_all_button_visible(self):
        self.assertTrue(self.client.login(username='test_user'))
        contest = Contest.objects.get()
        url = reverse('contest_dashboard', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Show all')
