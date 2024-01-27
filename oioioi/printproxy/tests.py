from django.urls import reverse

from oioioi.base.tests import TestCase
from oioioi.sinolpack.tests import get_test_filename


class TestPrintproxy(TestCase):
    fixtures = ['test_users',]

    def test_printproxy(self):
        url = reverse('noncontest:printproxy')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.client.login(username='test_admin'))
        resp = self.client.get(url)
        self.assertContains(resp, 'File to print')
        # Beware that this needs to be in data= instead of files=.
        resp = self.client.post(url, data={
            'file': open(get_test_filename('blank.pdf'), 'rb'),
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'File to print')
        self.assertContains(resp, 'Success!')
