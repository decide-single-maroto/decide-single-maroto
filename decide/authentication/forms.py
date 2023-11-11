from django import forms

class LoginForm(forms.Form):
    user = forms.CharField(label='Usuario')
    password = forms.Charfield(label='Contraseña', widget=forms.PasswordInput())