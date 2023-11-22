from django import forms

from oioioi.talent.models import TalentRegistration


class TalentRegistrationRoomForm(forms.ModelForm):
    class Meta:
        model = TalentRegistration
        fields = ['room',]
