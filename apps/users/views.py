# apps/users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout

from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

# Importations spécifiques à l'Auth Google (méthode ID Token)
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .serializers import (
    UserRegisterSerializer, 
    UserSerializer, 
    UserAvatarSerializer
)

User = get_user_model()


# =========================================================================
# 1. AUTHENTIFICATION DE BASE (Basée sur Simple JWT)
# =========================================================================

class UserRegisterView(generics.CreateAPIView):
    """
    Endpoint POST /api/v1/users/register/
    Permet l'enregistrement d'un nouvel utilisateur (email/password).
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Génère les tokens JWT immédiatement après l'inscription (Auto-login)
        user = serializer.instance
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                "message": _("Compte créé avec succès. Vous êtes maintenant connecté."), 
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            }, 
            status=status.HTTP_201_CREATED, 
        )


# =========================================================================
# 2. GESTION DU PROFIL (L'utilisateur connecté)
# =========================================================================

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Endpoint GET/PUT /api/v1/users/me/
    Permet de visualiser et mettre à jour le profil de l'utilisateur connecté.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# =========================================================================
# 3. LOGOUT (Blacklisting du Refresh Token)
# =========================================================================

class LogoutView(APIView):
    """
    Endpoint POST /api/v1/users/logout/
    Invalide la session en blacklistant le Refresh Token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": _("Déconnexion réussie.")}, status=status.HTTP_205_RESET_CONTENT)
            else:
                return Response(
                    {"detail": _("Token de rafraîchissement manquant.")}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            return Response(
                {"detail": _("Token de rafraîchissement invalide ou déjà utilisé.")}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# =========================================================================
# 4. GESTION DES FICHIERS (Avatar)
# =========================================================================

class AvatarUploadView(APIView):
    """
    Endpoint PATCH /api/v1/users/me/avatar/
    Permet de télécharger l'avatar de l'utilisateur.
    """
    parser_classes = [MultiPartParser, FormParser]  
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        
        if 'avatar' not in request.FILES:
            return Response(
                {"avatar": _("Veuillez fournir un fichier d'image.")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = UserAvatarSerializer(
            user, 
            data={'avatar': request.FILES['avatar']}, 
            partial=True
        )
            
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data) 
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================================================================
# 5. AUTHENTIFICATION GOOGLE (MÉTHODE ID TOKEN) - VERSION CORRIGÉE
# =========================================================================

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def google_auth(request):
    """
    Endpoint POST /api/v1/users/google-auth/
    Vérifie le jeton ID envoyé par le frontend et connecte l'utilisateur.
    """
    id_token_str = request.data.get("id_token")
    
    if not id_token_str:
        return Response({"error": "Jeton manquant"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Validation du jeton auprès de Google
        # Cela garantit que les infos (email, nom) ne sont pas falsifiées
        id_info = id_token.verify_oauth2_token(
            id_token_str, 
            google_requests.Request(), 
            settings.GOOGLE_OAUTH_CLIENT_ID
        )

        email = id_info.get('email')
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')
        
        if not email:
            return Response({"error": "Email non fourni par Google"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gestion de l'utilisateur en DB
        user, created = User.objects.get_or_create(email=email)
        
        if created:
            user.username = email 
            user.first_name = first_name
            user.last_name = last_name
           
            if hasattr(user, 'registration_method'):
                user.registration_method = 'google'
            user.set_unusable_password()
            user.save()
        else:
            # Sécurité: empêche de bypasser un compte existant créé par mot de passe
            if hasattr(user, 'registration_method') and user.registration_method != 'google' and user.has_usable_password():
                 return Response({
                    "error": "Ce compte existe déjà avec un mot de passe classique."
                }, status=status.HTTP_403_FORBIDDEN)

        # 3. Authentification session Django (Pour les templates)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # 4. Génération JWT (Pour les appels API futurs)
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "redirect_url": "/"
        }, status=status.HTTP_200_OK)

    except ValueError:
        return Response({"error": "Jeton Google invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# =========================================================================
# 6. VUES BASIQUES POUR L'INSCRIPTION ET LA CONNEXION (Django Forms)
# =========================================================================

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Connexion automatique après inscription
            return redirect('core:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {
        'form': form,
        'GOOGLE_OAUTH_CLIENT_ID': settings.GOOGLE_OAUTH_CLIENT_ID
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('core:home')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {
        'form': form,
        'GOOGLE_OAUTH_CLIENT_ID': settings.GOOGLE_OAUTH_CLIENT_ID
    })


def logout_view(request):
    logout(request)
    return redirect('core:home')