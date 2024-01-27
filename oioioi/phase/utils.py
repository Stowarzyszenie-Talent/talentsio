from oioioi.base.permissions import make_request_condition


@make_request_condition
def is_phase_contest(request):
    return hasattr(request.contest, 'controller') and getattr(
        request.contest.controller,
        'is_phase_contest',
        False,
    )
