from django.template.loader import get_template
from django.utils import timezone

from oioioi.base.permissions import enforce_condition
from oioioi.base.utils.pdf import generate_pdf
from oioioi.contests.utils import contest_exists, is_contest_admin
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
