#apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.conf import settings
from django.http import JsonResponse
import json

# Imports pour Google OAuth
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import User

# =========================================================================
# 1. INSCRIPTION (HTML)
# =========================================================================
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('core:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {
        'form': form,
        'GOOGLE_OAUTH_CLIENT_ID': settings.GOOGLE_OAUTH_CLIENT_ID
    })

# =========================================================================
# 2. CONNEXION (HTML Class-Based)
# =========================================================================
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['GOOGLE_OAUTH_CLIENT_ID'] = settings.GOOGLE_OAUTH_CLIENT_ID
        return context

# =========================================================================
# 3. DÉCONNEXION
# =========================================================================
from django.contrib.auth.decorators import login_required
@login_required
def logout_view(request):
    """Affiche une page de confirmation avant de déconnecter."""
    if request.method == 'POST':
        logout(request)
        return redirect('core:home')
    
    # Si c'est un GET, on affiche le template de confirmation
    return render(request, 'users/logout.html')

# =========================================================================
# 4. GOOGLE AUTH (AJAX - Appelée par le JS)
# =========================================================================
def google_auth_view(request):
    """
    Endpoint pour le bouton "Se connecter avec Google".
    Reçoit le token ID, valide avec Google, connecte l'utilisateur et renvoie du JSON.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        id_token_str = data.get("id_token")
        
        if not id_token_str:
            return JsonResponse({"error": "Jeton manquant"}, status=400)

        # 1. Validation du token via les serveurs Google
        id_info = id_token.verify_oauth2_token(
            id_token_str, 
            google_requests.Request(), 
            settings.GOOGLE_OAUTH_CLIENT_ID
        )

        email = id_info.get('email')
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')
        
        if not email:
            return JsonResponse({"error": "Email non fourni par Google"}, status=400)

        # 2. Création ou récupération de l'utilisateur
        user, created = User.objects.get_or_create(email=email)
        
        if created:
            user.username = email
            user.first_name = first_name
            user.last_name = last_name
            user.registration_method = 'google'
            user.set_unusable_password()
            user.save()
        else:
            # Sécurité : Pas de bypass de compte email classique
            if user.registration_method != 'google' and user.has_usable_password():
                 return JsonResponse({
                    "error": "Ce compte existe déjà avec un mot de passe. Connectez-vous avec votre email."
                }, status=403)

        # 3. Connexion session Django
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # 4. Réponse succès
        return JsonResponse({
            "success": True,
            "redirect_url": "/" 
        }, status=200)

    except ValueError:
        return JsonResponse({"error": "Jeton Google invalide ou expiré"}, status=400)
    except Exception as e:
        # Log l'erreur en prod
        return JsonResponse({"error": "Une erreur serveur est survenue"}, status=500)
    

