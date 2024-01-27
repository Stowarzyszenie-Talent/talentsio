from django.utils.translation import gettext_lazy as _

from oioioi.base import admin
from oioioi.contests.current_contest import reverse


admin.system_admin_menu_registry.register(
    'printproxy',
    _("Printing"),
    lambda request: reverse('printproxy'),
    order=60,
)
