from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from oioioi.base.permissions import enforce_condition
from oioioi.contests.utils import contest_exists

@require_POST
@enforce_condition(contest_exists)
def change_phase_ranking_type(request, key, rtype):
    rc = request.contest.controller.ranking_controller()
    if rtype not in getattr(rc, 'RANKING_TYPES', []):
        raise SuspiciousOperation
    # We can't directly alter stuff in the session
    rtype_dict = request.session.get('ranking_type', {})
    rtype_dict[request.contest.id] = rtype
    request.session['ranking_type'] = rtype_dict
    return redirect('ranking', key=key)
