from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date

# --- 1. FONCTIONS DE VALIDATION ---

def validate_is_adult(value):
    """Vérifie si la date de naissance correspond à un âge >= 18 ans"""
    if value:
        today = date.today()
        # Calcul de l'âge : année actuelle - année de naissance
        # On soustrait 1 si l'anniversaire n'est pas encore passé cette année
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValidationError(_("Vous devez avoir au moins 18 ans pour vous inscrire."))

# --- 2. MODÈLE PROFIL ---

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

    # Relation 1-to-1 avec l'utilisateur (User)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )

    # Identité
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        validators=[validate_is_adult], 
        verbose_name=_("Date de naissance")
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name=_("Biographie"))

    # Localisation
    city = models.CharField(max_length=100, verbose_name=_("Ville"))
    country = models.CharField(max_length=100, verbose_name=_("Pays"))
    is_diaspora = models.BooleanField(default=False, verbose_name=_("Vit à l'étranger"))

    # Préférences
    relationship_goal = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default="serious",
        verbose_name=_("Recherche")
    )

    # Modération et présence
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Profil")
        verbose_name_plural = _("Profils")
        # Index pour optimiser les performances de la recherche (SQL)
        indexes = [
            models.Index(fields=['gender']),
            models.Index(fields=['city']),
            models.Index(fields=['is_diaspora']),
            models.Index(fields=['relationship_goal']),
        ]

    @property
    def age(self):
        """Calcule l'âge dynamiquement pour l'affichage (Template)"""
        if not self.date_of_birth:
            return 18
        today = date.today()
        calculated_age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        # On sécurise l'affichage à 18 ans minimum
        return max(18, calculated_age)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.city})"

# --- 3. MODÈLES LIÉS (IMAGES, VUES, LIKES) ---

class ProfileImage(models.Model):
    """Galerie photo des utilisateurs"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="profile_images/", verbose_name=_("Photo"))
    is_cover = models.BooleanField(default=False, verbose_name=_("Photo de couverture"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', '-created_at']
        verbose_name = _("Photo de profil")
        verbose_name_plural = _("Photos de profil")

class ProfileView(models.Model):
    """Historique des visites sur les profils"""
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_views'
    )
    viewed_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='views'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['viewed_profile', '-viewed_at']),
        ]

class Like(models.Model):
    """Système de Like/Match"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="likes_given"
    )
    liked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="likes_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'liked_user')