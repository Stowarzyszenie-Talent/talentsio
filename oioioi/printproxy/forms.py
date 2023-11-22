from django import forms
from django.utils.translation import gettext_lazy as _


class PrintproxyForm(forms.Form):
    file = forms.FileField(
        label=_("File to print"),
        required=True,
    )
