from django.urls import re_path

from oioioi.talent import views

app_name = 'talent'

contest_patterns = [
    re_path(r'make_att_list_pdf/',
        views.make_att_list_pdf,
        name='make_att_list_pdf',
    ),
]
