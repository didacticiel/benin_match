from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Formulaire de contact.
    Utilisé sur la page publique.
    """
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'subject', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Votre email'}),
            'subject': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Pourquoi nous contactez-vous ?'}),
            'message': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full h-32', 'placeholder': 'Votre message...'}),
        }
        labels = {
            'full_name': 'Nom complet',
            'email': 'Adresse email',
            'subject': 'Sujet',
            'message': 'Message'
        }