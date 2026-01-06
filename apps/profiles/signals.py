#apps/profiles/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Signal unique pour gérer le profil utilisateur.
    On utilise get_or_create pour être certain de ne jamais tenter 
    une double insertion.
    """
    if created:
        # Calculer une date par défaut (18 ans en arrière)
        default_dob = date.today() - timedelta(days=18*365)
        
        # On utilise get_or_create au lieu de .create()
        # Cela vérifie si le profil existe AVANT d'essayer de l'insérer
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'date_of_birth': default_dob,
                'gender': 'M',
                'city': 'Cotonou',
                'country': 'Bénin',
                'relationship_goal': 'serious'
            }
        )
    else:
        # Si c'est une mise à jour de l'User, on sauvegarde le profil s'il existe
        if hasattr(instance, 'profile'):
            instance.profile.save()