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
    
    # On force Django à utiliser l'email comme identifiant unique
    USERNAME_FIELD = "email"
    # Le username est requis par défaut dans AbstractUser
    REQUIRED_FIELDS = ["username", "first_name", "last_name"] 

    # --- Champs Profil ---
    first_name = models.CharField(_("Prénom"), max_length=150, blank=False, null=False)
    last_name = models.CharField(_("Nom"), max_length=150, blank=False, null=False)
    
    registration_method = models.CharField(
        _("Méthode d'enregistrement"),
        max_length=20, 
        default='email',
        editable=False, # On ne change pas la méthode a posteriori
    )
    
    avatar = models.ImageField(
        _("Avatar / Photo de profil"), 
        upload_to='avatars/', 
        null=True, 
        blank=True,
        default='avatars/default.png'
    )

    def get_full_name(self):
        """Retourne le prénom et nom avec une majuscule"""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def __str__(self):
        return self.email