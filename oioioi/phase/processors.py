

def phase_processor(request):
    # This is unset in really weird circumstances like /force_error
    if not getattr(request, 'contest', False):
        return {}
    cc = request.contest.controller
    is_phased = getattr(cc, 'is_phase_contest', False)
    if is_phased:
        rc = cc.ranking_controller()
        rtype = rc.get_type(request)
    else:
        rtype = 'default'
    if rtype == 'default':
        rtype_name = ""
    else:
        rtype_name = rc.TYPE_NAMES[rtype]
    return {
        'is_phased': is_phased,
        'phase_ranking_type': rtype,
        'phase_ranking_type_name': rtype_name,
    }
