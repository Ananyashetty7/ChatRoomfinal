from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Room, User, Message


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'name', 'username', 'email', 'bio']


class MessageForm(forms.ModelForm):
    # Add file field for file uploads
    file = forms.FileField(required=False)  # Optional file field

    class Meta:
        model = Message
        fields = ['body', 'file']  # Include both body and file in the form fields
