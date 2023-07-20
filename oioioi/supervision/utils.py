from oioioi.supervision.models import Supervision


def can_user_enter_round(request_or_context, round):
    ensure_supervision(request_or_context)
    id = getattr(round, 'id', None)
    if request_or_context.is_under_supervision:
        return id in request_or_context.supervision_visible_rounds
    return id not in request_or_context.supervision_hidden_rounds


def ensure_supervision(request_or_context):
    if hasattr(request_or_context, 'is_under_supervision'):
        return
    request_or_context.is_under_supervision = False
    request_or_context.supervised_contests = set()
    request_or_context.supervision_hidden_rounds = set()
    request_or_context.supervision_visible_rounds = set()
    # there is no user for rankings (where else?), so we skip this.
    if not hasattr(request_or_context, 'timestamp') \
        or not hasattr(request_or_context, 'user') \
        or request_or_context.user.is_superuser:
        return

    relevant = Supervision.objects.filter(
        start_date__lte = request_or_context.timestamp,
        end_date__gt = request_or_context.timestamp,
    )
    rlist = relevant.filter(
        group__membership__user_id=request_or_context.user.id,
        group__membership__is_present=True,
    ).values_list('round__contest_id', 'round_id')

    request_or_context.is_under_supervision = len(rlist)>0
    if request_or_context.is_under_supervision:
        for c,r in rlist:
            request_or_context.supervision_visible_rounds.add(r)
            request_or_context.supervised_contests.add(c)
    else:
        request_or_context.supervision_hidden_rounds = set(
            relevant.values_list('round_id', flat=True))
