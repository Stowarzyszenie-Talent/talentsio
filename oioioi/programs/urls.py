from django.urls import include, re_path

from oioioi.programs import views

app_name = 'programs'

userout_patterns = [
    re_path(
        r'^generate/one/(?P<testreport_id>\d+)/$',
        views.generate_user_output_view,
        name='generate_user_output',
    ),
    re_path(
        r'^generate/all/(?P<submission_report_id>\d+)/$',
        views.generate_user_output_view,
        name='generate_user_output',
    ),
    re_path(
        r'^download/one/(?P<testreport_id>\d+)/$',
        views.download_user_one_output_view,
        name='download_user_output',
    ),
    re_path(
        r'^download/all/(?P<submission_report_id>\d+)/$',
        views.download_user_all_output_view,
        name='download_user_output',
    ),
]

urlpatterns = [
    re_path(
        r'^tests/(?P<test_id>\d+)/in/$',
        views.download_input_file_view,
        name='download_input_file',
    ),
    re_path(
        r'^tests/(?P<test_id>\d+)/out/$',
        views.download_output_file_view,
        name='download_output_file',
    ),
    re_path(
        r'^checker/(?P<checker_id>\d+)/$',
        views.download_checker_exe_view,
        name='download_checker_file',
    ),
    re_path(r'^userout/', include(userout_patterns)),
    re_path(
        r'^s/(?P<submission_id>\d+)/source/$',
        views.show_submission_source_view,
        name='show_submission_source',
    ),
    re_path(
        r'^s/(?P<submission_id>\d+)/download/$',
        views.download_submission_source_view,
        name='download_submission_source',
    ),
    re_path(
        r'^s/(?P<submission_id>\d+)/diffsave/$',
        views.save_diff_id_view,
        name='save_diff_id',
    ),
    re_path(
        r'^diff/(?P<submission1_id>\d+)/(?P<submission2_id>\d+)/$',
        views.source_diff_view,
        name='source_diff',
    ),
    re_path(
        r'^get_compiler_hints/$',
        views.get_compiler_hints_view,
        name='get_compiler_hints',
    ),
    re_path(
        r'^get_language_hints/$',
        views.get_language_hints_view,
        name='get_language_hints',
    ),
]
