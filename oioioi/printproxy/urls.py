from django.urls import re_path

from oioioi.printproxy import views

app_name = 'printproxy'

noncontest_patterns = [
    re_path(r'printproxy/',
        views.printproxy,
        name='printproxy',
    ),
]
