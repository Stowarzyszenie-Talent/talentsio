from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oioioi.base import admin


admin.system_admin_menu_registry.register(
    'printproxy',
    _("Printing"),
    lambda request: reverse('printproxy'),
    order=60,
)
