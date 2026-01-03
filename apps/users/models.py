# apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

REGISTRATION_CHOICES = [
    ('email', _('Email & Password')), 
    ('google', _('Google OAuth')),    
]

class User(AbstractUser):
    
    # --- Champs d'Authentification ---
    email = models.EmailField(_("adresse e-mail"), unique=True, null=False, blank=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 

    # --- Champs pour le Profil ---
    
    first_name = models.CharField(_("Prénom"), max_length=150, blank=False, null=False)
    last_name = models.CharField(_("Nom"), max_length=150, blank=False, null=False)
    
    registration_method = models.CharField(
        _("Méthode d'enregistrement"),
        max_length=20, 
        choices=REGISTRATION_CHOICES, 
        default='email',
        help_text=_("Méthode utilisée par l'utilisateur pour créer son compte.")
    )
    
    avatar = models.ImageField(
        _("Avatar / Photo de profil"), 
        upload_to='avatars/', 
        null=True, 
        blank=True,
        help_text=_("Image de profil de l'utilisateur. Stockée dans le dossier 'avatars/'.")
    )
    
    # Ajout d'une méthode str pour la lisibilité
    def __str__(self):
        return self.email
