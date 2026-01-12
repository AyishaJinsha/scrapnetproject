from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['registration_number', 'vehicle_type', 'age', 'mileage', 'image']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC-123'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Sedan, SUV'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }