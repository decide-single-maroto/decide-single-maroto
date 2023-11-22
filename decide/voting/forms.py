from django import forms
from .models import Question, QuestionOption

class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['number','option']

QuestionOptionFormSet = forms.inlineformset_factory(Question, QuestionOption, form=QuestionOptionForm, extra=2, can_delete=True)

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['desc', 'cattegory']

    options = QuestionOptionFormSet()