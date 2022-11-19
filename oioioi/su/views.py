from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from oioioi.base.permissions import enforce_condition, is_superuser
from oioioi.base.utils.redirect import safe_redirect
from oioioi.base.utils.user_selection import get_user_hints_view
from oioioi.status.registry import status_registry
from oioioi.su.forms import SuForm
from oioioi.su.middleware import REDIRECTION_AFTER_SU_KEY
from oioioi.su.utils import (
    is_real_superuser,
    is_under_su,
    reset_to_real_user,
    su_to_user,
)


@enforce_condition(is_superuser)
@require_POST
def su_view(request, next_page=None, redirect_field_name=REDIRECT_FIELD_NAME):
    form = SuForm(request.POST)
    if not form.is_valid():
        return TemplateResponse(
            request,
            'simple-centered-form.html',
            {
                'form': form,
                'action': reverse('su'),
                'title': _("Login as another user"),
            },
        )

    user = form.cleaned_data['user']
    if is_under_su(request):
        raise SuspiciousOperation

    su_to_user(request, user, form.cleaned_data['backend'])

    if redirect_field_name in request.GET:
        next_page = request.GET[redirect_field_name]
    elif redirect_field_name in request.POST:
        next_page = request.POST[redirect_field_name]

    request.session[REDIRECTION_AFTER_SU_KEY] = 'PRE_SU'

    return safe_redirect(request, next_page)


@enforce_condition(is_under_su)
@require_POST
def su_reset_view(request, next_page=None, redirect_field_name=REDIRECT_FIELD_NAME):
    reset_to_real_user(request)
    if redirect_field_name in request.GET:
        next_page = request.GET[redirect_field_name]
    elif redirect_field_name in request.POST:
        next_page = request.POST[redirect_field_name]

    return safe_redirect(request, next_page)


@enforce_condition(is_superuser)
def get_suable_users_view(request):
    users = User.objects.filter(is_superuser=False, is_active=True)
    return get_user_hints_view(request, 'substr', users)


@status_registry.register
def get_su_status(request, response):
    response['is_real_superuser'] = is_real_superuser(request)
    response['is_under_su'] = is_under_su(request)
    response['real_user'] = request.real_user.username
    if is_real_superuser(request):
        response['sync_time'] = min(10000, response.get('sync_time', 10000))

    return response
