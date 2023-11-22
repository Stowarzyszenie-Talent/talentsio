from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oioioi.base.menu import account_menu_registry
from oioioi.base.permissions import (
    enforce_condition,
    make_request_condition,
    not_anonymous,
)
from oioioi.base.utils.pdf import generate_pdf
from oioioi.contests.utils import contest_exists, is_contest_admin
from oioioi.talent.forms import TalentRegistrationRoomForm
from oioioi.talent.models import TalentRegistration

@enforce_condition(contest_exists & is_contest_admin)
def make_att_list_pdf(request):
    qs = TalentRegistration.objects.filter(
        contest_id=request.contest.id,
    ).order_by('user__last_name').select_related('user')
    date = timezone.now().strftime("%d.%m.%Y")
    tex_code = get_template("talent/attendance_list.tex").render(context={
        'participants': qs,
        'contest': request.contest,
        'curr_date': date,
    })
    return generate_pdf(
        tex_code,
        "obecnosc_{}_{}.pdf".format(date, request.contest.id.upper()),
    )


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
