from django.conf import settings
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oioioi.base.permissions import make_request_condition
from oioioi.base.utils import make_html_link
from oioioi.contests.admin import contest_site, contest_admin_menu_registry
from oioioi.talent.models import TalentRegistration
from oioioi.talent.utils import set_talent_participant


MOVE_ACTION_PREFIX = 'move_to_'

def move_wrapper(modeladmin, request, queryset):
    action_name = request.POST['action']
    assert action_name.startswith(MOVE_ACTION_PREFIX)
    cid = action_name[len(MOVE_ACTION_PREFIX):]
    for obj in queryset:
        set_talent_participant(obj.user, cid)
    messages.success(request, _("Success!"))


class TalentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['user_full_name',]
    ordering = ['user__last_name',]
    search_fields = ['user__username', 'user__last_name',]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Copied from participants/admin.py
    def user_full_name(self, instance):
        if not instance.user:
            return ''
        return make_html_link(
            reverse(
                'user_info',
                kwargs={'contest_id': instance.contest_id, 'user_id': instance.user_id},
            ),
            instance.user.get_full_name(),
        )

    user_full_name.short_description = _("User name")
    user_full_name.admin_order_field = 'user__last_name'

    def get_queryset(self, request):
        qs = super(TalentRegistrationAdmin, self).get_queryset(request)
        return qs.filter(contest_id=request.contest.id)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            actions.pop('delete_selected')
        for id in settings.TALENT_CONTEST_IDS:
            # Skip the current contest
            if id == request.contest.id:
                continue
            short_name = MOVE_ACTION_PREFIX + id
            actions[short_name] = (
                move_wrapper,
                short_name,
                _("Move to %(contest_name)s") % {
                    'contest_name': settings.TALENT_CONTEST_NAMES[id],
                },
            )
        return actions


@make_request_condition
def is_talent_registration_contest(request):
    return request.contest.id in settings.TALENT_CONTEST_IDS


contest_site.contest_register(TalentRegistration, TalentRegistrationAdmin)
contest_admin_menu_registry.register(
    'talentregistration_change',
    _("Talent participants"),
    lambda request: reverse('oioioiadmin:talent_talentregistration_changelist'),
    condition=is_talent_registration_contest,
    order=45,
)
