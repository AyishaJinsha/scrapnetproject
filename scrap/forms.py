from django import forms
from django.core.validators import RegexValidator
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    registration_number = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}-[0-9]{2}-[A-Z]{2}-[0-9]{4}$',
                message="Enter a valid vehicle registration number (Example: KL-07-AB-1234)"
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'KL-07-AB-1234'})
    )

    class Meta:
        model = Vehicle
        fields = ['registration_number', 'vehicle_type', 'age', 'mileage', 'image']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'email', 'username']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Full Name'})
        self.fields['first_name'].label = "Full Name"
        self.fields['email'].widget.attrs.update({'placeholder': 'example@email.com'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username'})
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})