from django import forms
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import get_user_model


User = get_user_model()



class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    ip_address = forms.CharField(widget=forms.HiddenInput)




class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=40,required=False,help_text='optional')
    last_name = forms.CharField(max_length=40,required=False,help_text='optional')
    email = forms.CharField(max_length=120,help_text='Required Submit a valid email address')
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','password1','password2',)



class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email',)



