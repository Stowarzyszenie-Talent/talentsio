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


class TalentRegistrationGenAttForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = self.get_initial_date()
    def get_initial_date(self):
        today = timezone.now().date()
        closest_contest = Contest.objects.filter(round__start_date__gt=today).order_by('round__start_date').first()

        if closest_contest:
            return closest_contest.round_set.order_by('start_date').first().start_date.strftime('%d.%m.%Y')
        else:
            return today.strftime('%d.%m.%Y')
            
    date = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date'},
        ),
        initial=get_initial_date(forms.Form),
    )
