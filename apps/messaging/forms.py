from django import forms
from .models import Message

class MessageForm(forms.Form):
    content = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            'rows': 1, 
            'class': 'textarea textarea-bordered w-full rounded-xl',
            'placeholder': 'Écrivez votre message...',
            'hx-post': True, 
            'hx-indicator': '#sending-indicator' # Indicateur de chargement HTMX
        })
    )
    image = forms.ImageField(
        label="Photo",
        required=False,
        widget=forms.FileInput(attrs={'class': 'file-input file-input-bordered'})
    )