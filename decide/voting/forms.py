from django import forms
from .models import Voting, Auth,Question, QuestionOption

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


class EditVotingForm(forms.ModelForm):
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
class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['number','option']

QuestionOptionFormSet = forms.inlineformset_factory(Question, QuestionOption, form=QuestionOptionForm, extra=1, can_delete=True)

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['desc', 'cattegory']

    options = QuestionOptionFormSet()
