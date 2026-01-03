# apps/users/urls_api.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserRegisterView, UserDetailView, AvatarUploadView, LogoutView, google_auth

app_name = 'users_api'

urlpatterns = [
   # ----------------------------------------------------
    # 1. Authentification de Base (JWT)
    # ----------------------------------------------------
    
    # POST /api/v1/users/register/ (Inscription)
    path("register/", UserRegisterView.as_view(), name="user-register"),
    
    # POST /api/v1/users/login/ (Connexion email/password)
    path('login/', TokenObtainPairView.as_view(), name='token-obtain-pair'), # <-- AJOUTÉ
    
    # POST /api/v1/users/token/refresh/ (Renouvellement)
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'), # <-- AJOUTÉ
    
    # POST /api/v1/users/logout/ (Déconnexion/Blacklist du refresh token)
    path("logout/", LogoutView.as_view(), name="user-logout"),
    
    # ----------------------------------------------------
    # 2. Gestion du Profil et Avatar
    # ----------------------------------------------------
    
    # GET/PUT/PATCH /api/v1/users/me/ (Détails de l'utilisateur connecté)
    path("me/", UserDetailView.as_view(), name="user-detail"),
    
    # PATCH /api/v1/users/me/avatar/ (Téléchargement et mise à jour de l'avatar)
    path("me/avatar/", AvatarUploadView.as_view(), name="avatar-upload"),
    
    # ----------------------------------------------------
    # 3. Authentification Sociale
    # ----------------------------------------------------
    
    # POST /api/v1/users/google-auth/ (Connexion/Inscription via Google ID Token)
    #path("google-auth/", google_auth, name="google-auth-id-token"),
    path("google-auth/", google_auth, name="google_auth"),
]