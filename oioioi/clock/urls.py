from django.urls import re_path

from oioioi.clock import views

app_name = 'clock'

urlpatterns = [
    re_path(r'^admin/time/$', views.admin_time, name='admin_time'),
    # Don't use the 'admin/' prefix, as that sometimes results in breakage.
    re_path(r'^admin_time/$', views.admin_time, name='admin_time'),
]
