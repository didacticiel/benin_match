# apps/messaging/forms.py
from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    content = forms.CharField(
        required=False,  # Important : le texte n'est plus obligatoire
        widget=forms.Textarea(attrs={
            'class': 'message-textarea w-full',
            'placeholder': 'Écrivez votre message...',
            'rows': 1,
            'style': 'resize: none;'
        })
    )
    
    image = forms.ImageField(
        required=False,  # Important : l'image n'est pas obligatoire
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'hidden'
        })
    )
    
    class Meta:
        model = Message
        fields = ['content', 'image']
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        
        # Vérifier qu'au moins un des deux champs est rempli
        if not content and not image:
            raise forms.ValidationError(
                "Veuillez écrire un message ou sélectionner une photo"
            )
        
        return cleaned_data