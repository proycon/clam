from django import forms
from clamopener.models import CLAMUsers
from django.core.validators import validate_email
from clamopener import settings

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

def pwhash(user, password):
    #computes a password hash for a given user and plaintext password
    return md5(user + ':' + django.settings.REALM + ':' + password).hexdigest()

class RegisterForm(forms.ModelForm):
    mail = forms.EmailField( label='E-Mail',max_length = 255 ,required=True)
    password2 = forms.CharField(label="Password (again)",  widget=forms.PasswordInput, max_length = 60, required=True )    
        
    class Meta:
        model = CLAMUsers
        fields = ('username', 'fullname', 'institution','mail','password')
        widgets = {
            'password': forms.PasswordInput,
            'password2': forms.PasswordInput,
        }
        


    def clean(self):
        cleaned_data = self.cleaned_data
        password = cleaned_data.get("password")    
        password2 = cleaned_data.get("password2")

        if password != password2:
            raise forms.ValidationError("Passwords don't match")
        
        #hash the passwords
        username = cleaned_data['username']
        cleaned_data['password'] = pwhash(username,password)
        
        # Always return the full collection of cleaned data.
        return cleaned_data
    
        
#class RegisterForm(forms.Form):
    #username = forms.CharField(label="Username", max_length = 60, required=True)
    #password = forms.CharField(label="Password", widget=forms.PasswordInput, max_length = 60, required=True )
    #password2 = forms.CharField(label="Password (again)",  widget=forms.PasswordInput, max_length = 60, required=True )
    #fullname = forms.CharField(label="Full name" max_length = 255, required=True )
    #institution = forms.CharField(label="Institution", max_length = 255 )
    #mail = forms.EmailField(label="E-mail", max_length = 255, required=True )
