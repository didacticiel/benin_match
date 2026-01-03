from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # On ne garde que 'email'. 
        # Django ajoutera automatiquement les champs password1 et password2.
        fields = ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Comme le champ 'username' est obligatoire dans le modèle Django par défaut,
        # on lui donne la valeur de l'email si vous ne demandez pas de pseudo.
        if not user.username:
            user.username = user.email
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email',)