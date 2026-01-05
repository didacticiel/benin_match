from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['gender', 'date_of_birth', 'city', 'country', 'is_diaspora', 'relationship_goal', 'bio']
        
        widgets = {
            'gender': forms.Select(attrs={'class': 'select select-bordered'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Ex: Cotonou'}),
            'country': forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Ex: Bénin'}),
            'bio': forms.Textarea(attrs={'class': 'textarea textarea-bordered h-32', 'placeholder': 'Parlez un peu de vous...'}),
            'relationship_goal': forms.Select(attrs={'class': 'select select-bordered'}),
            'is_diaspora': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }