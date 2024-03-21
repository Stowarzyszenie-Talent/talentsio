from django import forms
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from oioioi.talent.models import TalentRegistration

from oioioi.contests.models import Contest, Round

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


    date = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date'},
        ),
    )
