from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire d'inscription.
    Demande : Email, Prénom, Nom (plus les 2 mots de passe auto).
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name')
        
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'exemple@gmail.com',
                'class': 'input input-bordered' # Classe Tailwind
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Ton prénom',
                'class': 'input input-bordered'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Ton nom',
                'class': 'input input-bordered'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Génération du username si vide (basé sur l'email)
        if not user.username:
            user.username = self.cleaned_data.get('email').split('@')[0]
        user.registration_method = 'email'
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulaire de connexion modifié pour accepter l'EMAIL au lieu du username.
    """
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'autofocus': True, 
            'placeholder': 'email@exemple.com',
            'class': 'input input-bordered'
        })
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'input input-bordered'
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Traduction de l'erreur d'authentification
        self.error_messages['invalid_login'] = _(
            "Email ou mot de passe incorrect."
        )