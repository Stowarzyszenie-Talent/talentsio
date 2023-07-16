from django.urls import re_path

from oioioi.phase import views

app_name = 'phase'

contest_patterns = [
    re_path(r'^ranking/(?P<key>[a-z0-9_-]+)/phase_rtype/(?P<rtype>\w+)$',
        views.change_phase_ranking_type,
        name='change_phase_ranking_type',
    ),
]
