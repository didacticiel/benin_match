from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-white/5 border-white/10 focus:border-primary rounded-2xl', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full bg-white/5 border-white/10 focus:border-primary rounded-2xl', 'placeholder': 'votre@email.com'}),
            'subject': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-white/5 border-white/10 focus:border-primary rounded-2xl', 'placeholder': 'Sujet du message'}),
            'message': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full bg-white/5 border-white/10 focus:border-primary rounded-2xl h-32', 'placeholder': 'Comment puis-je vous aider ?'}),
        }