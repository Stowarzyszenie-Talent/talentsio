from django.urls import re_path

from oioioi.talent import views

app_name = 'talent'

contest_patterns = [
    re_path(r'make_att_list_pdf/',
        views.make_att_list_pdf,
        name='make_att_list_pdf',
    ),
    re_path(r'talent_camp_data/',
        views.talent_camp_data_view,
        name='talent_camp_data',
    ),
    re_path(r'talent_att_list_gen_view/',
        views.talent_att_list_gen_view,
        name='talent_att_list_gen_view',
    )
]
