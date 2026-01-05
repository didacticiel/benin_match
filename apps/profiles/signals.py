from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import Profile

User = get_user_model()

from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal qui crée un profil vide dès qu'un User est créé.
    """
    if created:
        # Créer le profil uniquement à la création du user
        # pour éviter de l'écraser s'il existe déjà
        Profile.objects.create(user=instance)
        


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal qui crée un profil vide dès qu'un User est créé.
    
    IMPORTANT : Comme 'date_of_birth' est obligatoire, on doit donner
    des valeurs par défaut ici si l'utilisateur vient du CLI (createsuperuser)
    ou si le formulaire d'inscription ne l'a pas fournie.
    """
    if created:
        # Calculer une date par défaut (18 ans en arrière)
        # Cela évite l'erreur IntegrityError lors de la création du superadmin
        default_dob = date.today() - timedelta(days=18*365)
        
        # Création du profil avec les valeurs requises pour satisfaire la BDD
        Profile.objects.create(
            user=instance,
            date_of_birth=default_dob, # Date obligatoire
            gender='M',                # Par défaut Homme
            city='Cotonou',            # Par défaut Cotonou
            country='Bénin',
            relationship_goal='serious'
        )