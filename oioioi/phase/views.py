import time

from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from oioioi.base.permissions import enforce_condition
from oioioi.contests.models import Round
from oioioi.contests.utils import contest_exists
from oioioi.phase.controllers import _FirstPhase
from oioioi.phase.models import Phase
from oioioi.status.registry import status_registry

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


@status_registry.register
def get_phases_status(request, response):
    """Extends the dictionary with keys:
    ``phase_start_date`` the number of seconds between the epoch
    and the end of the nearest-ending phase if any exists;
    otherwise 0
    ``phase_end_date`` the number of seconds between the epoch
    and the end of the nearest-ending phase if any exists;
    otherwise 0
    ``phase_round_name`` from the phase mentioned above
    ``phase_multiplier`` from the phase mentioned above
    """
    timestamp = getattr(request, 'timestamp', None)
    contest = getattr(request, 'contest', None)
    response.update(dict(
        phase_start_date=0,
        phase_end_date=0,
        phase_round_name="",
        phase_multiplier=0,
    ))

    next_rounds_times = None
    current_rounds_times = None

    if timestamp and contest:
        rounds = [
            round
            for round in Round.objects.filter(contest=contest)
            if contest.controller.can_see_round(request, round)
        ]
        # Ordered by start date by default
        next_phase = Phase.objects.filter(
            round_id__in=[r.id for r in rounds],
            start_date__gt=timestamp,
        ).first()
        if next_phase:
            end_date = next_phase.start_date
            current_phase = Phase.objects.filter(
                round_id=next_phase.round_id,
                start_date__lte=timestamp,
            ).last()
            if current_phase:
                start_date = current_phase.start_date
                multiplier = current_phase.multiplier
            else:
                start_date = next_phase.round.start_date
                multiplier = _FirstPhase.multiplier
            response['phase_multiplier'] = multiplier
            response['phase_round_name'] = next_phase.round.name
            response['phase_start_date'] = time.mktime(
                timezone.localtime(start_date).timetuple()
            )
            response['phase_end_date'] = time.mktime(
                timezone.localtime(end_date).timetuple()
            )

    return response
