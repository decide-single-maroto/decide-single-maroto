from django import forms
from .models import Voting

INPUT_CLASSES = 'w-full py-4 px-6 rounded-xl border'

class NewVotingForm(forms.ModelForm):
    class Meta:
        model = Voting
        fields = ('name','desc','question','model','seats',)

        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASSES
            }),
            'question': forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'model': forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'seats': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
        }
