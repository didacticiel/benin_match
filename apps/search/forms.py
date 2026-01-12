#apps/search/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _

# --- 1. FORMULAIRE DE RECHERCHE ---
class SearchForm(forms.Form):
    """
    Formulaire pour filtrer les profils.
    Utilisé pour la recherche HTMX (Live).
    """
    # Genre
    GENDER_CHOICES = [
        ('', _('Tous')),
        ('M', _('Homme')),
        ('F', _('Femme')),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False, widget=forms.Select(attrs={'class': 'select select-bordered w-full'}))

    # Type de Relation
    GOAL_CHOICES = [
        ('', _('Tout')),
        ('serious', _('Sérieux / Mariage')),
        ('friendship', _('Amitié')),
        ('dating', _('Rencontre légère')),
    ]
    relationship_goal = forms.ChoiceField(choices=GOAL_CHOICES, required=False, widget=forms.Select(attrs={'class': 'select select-bordered w-full'}))

    # Ville
    city = forms.CharField(
        label="Ville",
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Ex: Cotonou'})
    )

    # Âge (Min / Max) -> CORRECTION ICI
    # On met 'min' et 'max' dans les ATTRIBUTS WIDGET (HTML)
    min_age = forms.IntegerField(
        label="Âge min",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '18', 'min': '18', 'max': '100'})
    )
    max_age = forms.IntegerField(
        label="Âge max",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '100', 'min': '18', 'max': '100'})
    )

    # Checkbox Diaspora
    is_diaspora = forms.BooleanField(label="Vit à l'étranger (Diaspora)", required=False, widget=forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary mt-2'}))