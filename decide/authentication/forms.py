from django import forms

class LoginForm(forms.Form):
    user = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput())