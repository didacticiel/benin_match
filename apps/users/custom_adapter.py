# apps/users/custom_adapter.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptateur personnalisé pour gérer la connexion et l'inscription via des comptes sociaux.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Lie un compte social à un utilisateur existant si l'email correspond.
        """
        if sociallogin.is_existing:
            return

        if not sociallogin.email_addresses:
            return
        
        email = sociallogin.email_addresses[0].email
        
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Sauvegarde l'utilisateur et génère les tokens JWT.
        """
        user = super().save_user(request, sociallogin, form=form)
        
        # Génère les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Stocke les tokens dans sociallogin.state
        sociallogin.state['access_token'] = str(refresh.access_token)
        sociallogin.state['refresh_token'] = str(refresh)
        
        return user


class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """
    Adaptateur personnalisé pour Google OAuth2 avec la bonne URL de redirection.
    """
    
    def get_callback_url(self, request, app):
        """
        Retourne l'URL de callback qui correspond à celle configurée dans Google Console.
        """
        callback_url = f"{settings.FRONTEND_URL}/auth/social/callback"
        return callback_url
    
