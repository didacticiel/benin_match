from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q, Max
from django.urls import reverse_lazy
from datetime import date

from apps.profiles.models import Profile
from .forms import SearchForm

# --- VUE PRINCIPALE DE RECHERCHE ---
class SearchView(View):
    """
    Vue HTMX :
    - GET : Affiche la page avec formulaire et résultats par défaut.
    - POST : Renvoie SEULEMENT la grille HTML (Partial) pour mettre à jour instantanément.
    """
    template_name = "search/search.html"

    def get(self, request, *args, **kwargs):
        # Initialiser le formulaire avec les paramètres GET s'il y en a (ex: ?gender=F)
        form = SearchForm(request.GET)
        
        # Récupérer les profils
        profiles = Profile.objects.filter(is_active=True).select_related('user')
        profiles = self.apply_filters(form, profiles)
        
        # Pagination (Standard)
        profiles = profiles.order_by('-user__date_joined')[:20]

        return render(request, self.template_name, {
            'form': form,
            'profiles': profiles
        })

    def post(self, request, *args, **kwargs):
        """
        Recherche HTMX.
        """
        form = SearchForm(request.POST)
        
        # Récupérer les profils filtrés
        profiles = Profile.objects.filter(is_active=True).select_related('user')
        profiles = self.apply_filters(form, profiles)
        
        # Renvoyer SEULEMENT la grille HTML (Partial)
        # `hx-target="#search-results"` va remplacer la grille dans le DOM
        return render(request, 'search/partials/profile_list.html', {
            'profiles': profiles.order_by('-user__date_joined')[:50]
        })

    def apply_filters(self, form, queryset):
        """
        Applique les filtres au QuerySet.
        Gère à la fois GET (données brutes) et POST (cleaned_data).
        """
        # 1. Déterminer la source des données
        if form.is_valid():
            data = form.cleaned_data
        else:
            # Pour GET, clean_data n'existe pas encore. On utilise .data
            # On extrait uniquement les champs remplis pour éviter les requêtes vides.
            data = {}
            if form.data.get('gender'):
                data['gender'] = form.data['gender']
            if form.data.get('relationship_goal'):
                data['relationship_goal'] = form.data['relationship_goal']
            if form.data.get('city'):
                data['city'] = form.data['city']
            if form.data.get('is_diaspora'):
                data['is_diaspora'] = form.data['is_diaspora']
            if form.data.get('min_age'):
                data['min_age'] = form.data['min_age']
            if form.data.get('max_age'):
                data['max_age'] = form.data['max_age']

        # 2. Appliquer les filtres
        if data.get('gender'):
            queryset = queryset.filter(gender=data['gender'])
        
        if data.get('relationship_goal'):
            queryset = queryset.filter(relationship_goal=data['relationship_goal'])
        
        if data.get('city'):
            queryset = queryset.filter(city__icontains=data['city'])
        
        if data.get('is_diaspora'):
            queryset = queryset.filter(is_diaspora=True)

        # 3. Filtres d'âge (Calcul dynamique)
        today = date.today()
        if data.get('min_age'):
            max_dob = today.replace(year=today.year - int(data['min_age']))
            queryset = queryset.filter(date_of_birth__lte=max_dob)

        if data.get('max_age'):
            min_dob = today.replace(year=today.year - int(data['max_age']) - 1)
            queryset = queryset.filter(date_of_birth__gte=min_dob)
            
        return queryset