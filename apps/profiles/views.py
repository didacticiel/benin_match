from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, ListView  # AJOUTER ICI
from django.urls import reverse_lazy
from .models import Profile
from .forms import ProfileForm

# --- 1. LISTE DES PROFILS (PUBLIQUE) ---
class ProfileListView(ListView):
    """Affiche la grille des célibataires"""
    model = Profile
    template_name = "profiles/profile_list.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        # On affiche seulement les profils actifs, du plus récent au plus ancien
        # On utilise select_related pour éviter les requêtes SQL inutiles
        return Profile.objects.filter(is_active=True).select_related('user').order_by('-user__date_joined')

# --- 2. DÉTAIL D'UN PROFIL (PUBLIQUE) ---
class ProfileDetailView(DetailView):
    model = Profile
    template_name = "profiles/profile_detail.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupérer toutes les images du profil
        context['profile_images'] = self.object.images.all()
        return context

# --- 3. ÉDITION DU PROFIL (CONNECTÉ SEULEMENT) ---
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "profiles/profile_edit.html"
    success_url = reverse_lazy('profiles:my_profile') 

    def get_object(self):
        # S'assurer que l'utilisateur ne peut éditer que son propre profil
        return self.request.user.profile
    
# Ajoute dans apps/profiles/views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 1. Récupérer le profil de l'utilisateur
        try:
            profile = user.profile
        except AttributeError:
            # Gestion d'erreur si le profil n'existe pas encore
            profile = None

        # 2. Calculer la "Complétude" du profil (pourcentage)
        completion = 0
        if profile:
            if profile.gender: completion += 20
            if profile.city: completion += 20
            if profile.bio: completion += 20
            if profile.relationship_goal: completion += 20
            if profile.images.count() > 0: completion += 20
        
        # 3. Faux "Stats" (car les apps Search/Messaging ne sont pas finies)
        stats = {
            'visits': '12',    # On remplacera ça par des vraies données plus tard
            'new_likes': '5',
            'new_messages': '2'
        }

        context['profile'] = profile
        context['completion'] = completion
        context['stats'] = stats
        return context