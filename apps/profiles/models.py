from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):
    GENDER_CHOICES = [
        ("M", _("Homme")),
        ("F", _("Femme")),
    ]

    RELATIONSHIP_CHOICES = [
        ("serious", _("Relation Sérieuse")),
        ("marriage", _("Mariage")),
        ("friendship", _("Amitié")),
        ("dating", _("Rencontre légère")),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    
    # --- Identité ---
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(verbose_name=_("Date de naissance"))
    bio = models.TextField(max_length=500, blank=True, verbose_name=_("Biographie"))
    
    # --- Localisation ---
    city = models.CharField(max_length=100, verbose_name=_("Ville"))
    country = models.CharField(max_length=100, verbose_name=_("Pays"))
    is_diaspora = models.BooleanField(default=False, verbose_name=_("Vit à l'étranger"))
    
    # --- Préférences ---
    relationship_goal = models.CharField(
        max_length=20, 
        choices=RELATIONSHIP_CHOICES, 
        default="serious",
        verbose_name=_("Recherche")
    )
    
    # --- Moderation ---
    is_active = models.BooleanField(default=True) # Compte suspendu ou supprimé
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        # Index pour la performance des filtres
        indexes = [
            models.Index(fields=['gender']),
            models.Index(fields=['city']),
            models.Index(fields=['is_diaspora']),
            models.Index(fields=['relationship_goal']),
        ]

    @property
    def age(self):
        """Calcule l'âge dynamiquement"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.city})"


class ProfileImage(models.Model):
    """Pour gérer plusieurs photos par utilisateur"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="profile_images/", verbose_name=_("Photo"))
    is_cover = models.BooleanField(default=False, verbose_name=_("Photo de couverture"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', '-created_at']
        verbose_name = "Photo de profil"
        verbose_name_plural = "Photos de profil"