from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oioioi.base.menu import account_menu_registry
from oioioi.base.permissions import (
    enforce_condition,
    make_request_condition,
    not_anonymous,
)
from oioioi.base.navbar_links import navbar_links_registry
from oioioi.base.utils.pdf import generate_pdf
from oioioi.base.utils.execute import execute
from oioioi.contests.attachment_registration import attachment_registry
from oioioi.contests.models import Contest
from oioioi.contests.utils import contest_exists, is_contest_admin
from oioioi.talent.forms import TalentRegistrationRoomForm
from oioioi.talent.models import TalentRegistration
from oioioi.talent.forms import TalentRegistrationGenAttForm


if settings.CPPREF_URL != "":
    navbar_links_registry.register(
        name='cppreference',
        text=_("C++ reference"),
        url_generator=lambda request: settings.CPPREF_URL,
        order=440, # last
    )


@attachment_registry.register
def get_cppreference(request):
    if settings.CPPREF_URL == "":
        return []
    return [{
        'category': None,
        'name': 'cppreference',
        'description': _("C++ reference"),
        'link': settings.CPPREF_URL,
        'pub_date': datetime.utcfromtimestamp(0),
    }]


@make_request_condition
def has_talent_registration(request):
    if request.user.is_anonymous:
        return False
    return TalentRegistration.objects.filter(user=request.user).exists()


@account_menu_registry.register_decorator(
    _("My camp data"),
    lambda request: reverse('contest:talent_camp_data'),
    order=199, # order it just above logout
    condition=has_talent_registration,
)
@enforce_condition(not_anonymous & has_talent_registration)
def talent_camp_data_view(request):
    tr = TalentRegistration.objects.get(user=request.user)
    orig_room = tr.room
    form = TalentRegistrationRoomForm(instance=tr)
    if request.method == 'POST':
        form = TalentRegistrationRoomForm(request.POST, instance=tr)
        if form.is_valid():
            if orig_room != form.cleaned_data['room']:
                tr.room = form.cleaned_data['room']
                tr.save()
                messages.success(request, _("Successfully changed!"))
            else:
                messages.warning(request, _("Nothing has been changed."))
            return redirect('talent_camp_data')
    return TemplateResponse(
        request,
        'talent/camp_data.html',
        context={
            'form': form,
            'talent_registration': tr,
        },
    )


def make_att_list_pdf(contest, date):
    participants = list(TalentRegistration.objects.filter(
        contest_id=contest.id,
    ).order_by('user__last_name').select_related('user'))
    tex_code = get_template("talent/attendance_list.tex").render(context={
        'participants': participants,
        'contest': contest,
        'curr_date': datetime.strftime(date, "%d.%m.%Y"),
    })
    return (generate_pdf(
        tex_code,
        "obecnosc_{}_{}.pdf".format(date, contest.id.upper()),
    ), len(participants) > 0)


@enforce_condition(contest_exists & is_contest_admin)
def talent_att_list_gen_view(request, print_all=False):
    if request.method == 'POST':
        form = TalentRegistrationGenAttForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            if not print_all:
                pdf, _any_users = make_att_list_pdf(request.contest, date)
                return pdf
            for c in Contest.objects.filter(id__in=settings.TALENT_CONTEST_IDS).order_by('id'):
                pdf, any_users = make_att_list_pdf(c, date)
                if not any_users:
                    messages.warning(
                        request,
                        _("Not printing empty attendance list for contest %(contest)s.") % {"contest": c},
                    )
                    continue
                if getattr(settings, 'TESTS', False):
                    print(f"Printing attendance list for contest {c}.")
                else:
                    execute(['lp', '-o', 'media=a4'], stdin=b"".join(pdf.streaming_content))
            messages.success(request, _("Attendance lists sent for printing!"))
            return redirect('oioioiadmin:talent_talentregistration_changelist')

    closest_round = request.contest.round_set.filter(
        start_date__gt=request.timestamp - timedelta(hours=6),
    ).order_by('start_date').first()
    if closest_round is not None:
        initial_date = closest_round.start_date
    else:
        initial_date = request.timestamp
    form = TalentRegistrationGenAttForm(initial={'date': initial_date.date()})
    return TemplateResponse(
        request,
        'talent/make_att_list.html',
        context={
            'form': form,
        },
    )
