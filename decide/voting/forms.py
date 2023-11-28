from django import forms
from .models import Voting, Auth

INPUT_CLASSES = 'w-full py-4 px-6 rounded-xl border'

class NewVotingForm(forms.ModelForm):
    class Meta:
        model = Voting
        fields = ('name', 'desc', 'question', 'auths', 'model', 'seats')
        exclude = ['start_date', 'end_date', 'pub_key', 'tally', 'postproc']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
            'desc': forms.Textarea(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
            'question': forms.Select(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
            'auths': forms.SelectMultiple(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
            'model': forms.Select(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
            'seats': forms.NumberInput(attrs={'class': 'w-full py-4 px-6 rounded-xl border'}),
        }


class NewAuthForm(forms.ModelForm):
    class Meta:
        model = Auth
        fields = ('name', 'url', 'me')

        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'url': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'me': forms.CheckboxInput(attrs={
                'class': INPUT_CLASSES
            }),            
        }