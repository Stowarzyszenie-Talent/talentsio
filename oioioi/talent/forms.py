from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from oioioi.talent.models import TalentRegistration


class TalentRoomFormField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['label'] = _("room_number_desc")
        if 'validators' not in kwargs:
            kwargs['validators'] = []
        kwargs['validators'] += [
            RegexValidator(settings.TALENT_ROOM_REGEX)
        ]

        super(TalentRoomFormField, self).__init__(*args, **kwargs)


class TalentRegistrationRoomForm(forms.ModelForm):
    class Meta:
        model = TalentRegistration
        fields = ['room',]
        field_classes = {'room': TalentRoomFormField}


class TalentRegistrationGenAttForm(forms.Form):
    date = forms.DateField()
