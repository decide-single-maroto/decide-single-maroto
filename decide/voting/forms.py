from django import forms
from .models import Voting, Auth

INPUT_CLASSES = 'w-full py-4 px-6 rounded-xl border'

class NewVotingForm(forms.ModelForm):
    class Meta:
        model = Voting
        fields = ('name','desc','question','auths','model','seats',)

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
            'auths': forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'model': forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'seats': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
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
    
