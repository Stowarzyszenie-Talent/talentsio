from django.conf import settings
from django.urls import re_path

from oioioi.perfdata import api

app_name = 'perfdata'

noncontest_patterns = []
if settings.USE_API:
    noncontest_patterns.extend([
        re_path(
            r'^api/recent_submissions_number',
            api.recent_submissions_number,
            name='recent_submissions_number',
        ),
    ])
