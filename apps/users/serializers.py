# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.utils.translation import gettext_lazy as _

User = get_user_model()


# =========================================================================
# 1. ENREGISTREMENT (REGISTER)
# =========================================================================

class UserRegisterSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'un nouvel utilisateur (inscription classique)."""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = (
            'email', 
            'username', 
            'first_name', 
            'last_name', 
            'password', 
            'password2'
        )
        extra_kwargs = {
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        # 1. Vérification de la correspondance des mots de passe.
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": _("Les mots de passe ne correspondent pas.")})

        # 2. Préparation des données pour la validation du mot de passe.
        user_data_for_validation = {
            'email': data.get('email'),
            'username': data.get('username'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
        }

        # 3. Validation de la complexité du mot de passe via les règles de settings.py.
        try:
            # Passe l'instance de l'utilisateur temporaire pour la validation
            validate_password(data['password'], user=User(**user_data_for_validation)) 
        except django_exceptions.ValidationError as e:
            # Renvoie les messages d'erreur de Django.
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return data

    def create(self, validated_data):
        # Retire le champ 'password2' qui n'est pas un champ de modèle.
        validated_data.pop('password2')
        
        # Le champ 'registration_method' utilise la valeur par défaut 'email' du modèle.
        user = User.objects.create_user(
            **validated_data
        )
        return user

# =========================================================================
# 2. CONNEXION (LOGIN - basé sur email/password)
# Utilisé par les vues pour la validation des données d'entrée.
# =========================================================================

class LoginSerializer(serializers.Serializer):
    """Sérialiseur pour la connexion (email/password)."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

# =========================================================================
# 3. DÉTAILS DU PROFIL (GET/UPDATE /users/me/)
# * CHAMP 'is_premium_subscriber' RETIRÉ car non présent dans le modèle User.
# =========================================================================

class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la lecture et la mise à jour du profil utilisateur."""
    
    # Mappe le champ de fichier à une URL lisible
    avatar_url = serializers.ImageField(source='avatar', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'username', 
            'first_name', 
            'last_name', 
            'avatar_url', 
            'registration_method', # Ajout du champ pour la lisibilité
            'is_staff', 
            'date_joined'
        )
        # Champs que l'utilisateur ne peut pas modifier via cette API.
        read_only_fields = ('id', 'email', 'registration_method', 'is_staff', 'date_joined')
        
# =========================================================================
# 4. TÉLÉCHARGEMENT D'AVATAR (PATCH /users/me/avatar/)
# =========================================================================

class UserAvatarSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour du champ avatar uniquement."""
    class Meta:
        model = User
        fields = ('avatar',)
