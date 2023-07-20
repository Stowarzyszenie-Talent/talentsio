from django.template.loader import render_to_string

from oioioi.supervision.utils import ensure_supervision


def supervision_processor(request):
    ensure_supervision(request)
    is_under_supervision = request.is_under_supervision
    return {
        'is_under_supervision': is_under_supervision,
        'extra_navbar_right_supervision': render_to_string(
            'supervision/navbar-user-supervision.html',
            dict(is_under_supervision=is_under_supervision)),
    }
