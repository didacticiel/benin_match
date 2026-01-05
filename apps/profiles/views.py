from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, ListView  # AJOUTER ICI
from django.urls import reverse_lazy
from .models import Profile
from .forms import ProfileForm, ProfileImageForm
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from datetime import date, timedelta
from .models import Profile, ProfileImage


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
        
        # 1. Récupérer toutes les images du profil
        context['profile_images'] = self.object.images.all()
        
        # 2. Récupérer spécifiquement l'image marquée comme couverture
        try:
            # On cherche l'image où is_cover=True
            context['cover_image'] = self.object.images.get(is_cover=True)
        except ProfileImage.DoesNotExist:
            # S'il n'y a pas d'image de couverture, on met None
            context['cover_image'] = None
            
        return context

# --- 3. ÉDITION DU PROFIL (CONNECTÉ SEULEMENT) ---
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "profiles/profile_edit.html"
    success_url = reverse_lazy('profiles:dashboard') # Redirection vers le dashboard
    form_class = ProfileForm

    def get_object(self):
        """Récupère le profil ou le crée si inexistant"""
        try:
            return self.request.user.profile
        except:
            # Création avec valeurs par défaut pour éviter les erreurs IntegrityError
            from datetime import date, timedelta
            default_dob = date.today() - timedelta(days=18*365)
            profile = Profile.objects.create(
                user=self.request.user,
                date_of_birth=default_dob,
                gender='M',
                city='Cotonou'
            )
            return profile

    def get_context_data(self, **kwargs):
        """Envoie les deux formulaires (Profil et Image) au template"""
        context = super().get_context_data(**kwargs)
        
        # Initialiser le formulaire d'image avec None (vide)
        # (Si on passe request.FILES ici, Django va essayer de valider le formulaire sur le GET, ce qui est bizarre)
        context['image_form'] = ProfileImageForm() 
        
        # Récupérer l'image de couverture actuelle
        try:
            context['current_cover'] = self.object.images.get(is_cover=True)
        except ProfileImage.DoesNotExist:
            context['current_cover'] = None
            
        return context

    def post(self, request, *args, **kwargs):
        """
        Gère le POST avec deux formulaires séparés.
        """
        self.object = self.get_object()
        
        # 1. Instancier les deux formulaires avec les données POST
        form = ProfileForm(request.POST, instance=self.object)
        image_form = ProfileImageForm(request.POST, request.FILES)
        
        # Variables de succès
        profile_saved = False
        image_saved = False

        # 2. Validation et Sauvegarde
        if form.is_valid():
            form.save() # Sauvegarde le profil + nom/prénom
            profile_saved = True
        else:
            # Si le formulaire principal est invalide, on arrête tout.
            # On retourne la page avec les erreurs (les inputs files seront vides -> comportement normal)
            return self.form_invalid(form)

        # 3. Validation et Sauvegarde de l'Image (Indépendante)
        if image_form.is_valid():
            image_form.save(self.object)
            image_saved = True
        # Note : Si image_form n'est pas valide (ex: fichier corrompu), on ne fait rien, mais on ne bloque pas la sauvegarde du profil principal

        # 4. Redirection
        if profile_saved:
            return HttpResponseRedirect(self.get_success_url())
        elif image_saved:
            # Si seule l'image a été sauvegardée, on recharge la page pour l'afficher
            return HttpResponseRedirect(request.path_info)
        else:
            # Ne devrait pas arriver
            return self.form_invalid(form)

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