
from django import forms
from .models import Census

INPUT_CLASSES = 'w-full py-4 px-6 rounded-xl border'

class NewCensusForm(forms.ModelForm):
    class Meta:
        model = Census
        fields = ('voting_id','voter_id')

        
        
