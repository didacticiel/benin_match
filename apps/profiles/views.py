#apps/profiles/views.py
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, ListView, TemplateView
from django.urls import reverse_lazy
from .models import Profile, ProfileImage, ProfileView
from .forms import ProfileForm, ProfileImageForm
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from datetime import date, timedelta
from django.db.models import Count, Q, Max
from django.utils import timezone



# --- 1. LISTE DES PROFILS (PUBLIQUE) ---
class ProfileListView(ListView):
    """Affiche la grille des célibataires"""
    model = Profile
    template_name = "profiles/profile_list.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        # On affiche seulement les profils actifs, du plus récent au plus ancien
        return Profile.objects.filter(is_active=True).select_related('user').order_by('-user__date_joined')


# --- 2. DÉTAIL D'UN PROFIL (PUBLIQUE) ---
class ProfileDetailView(DetailView):
    model = Profile
    template_name = "profiles/profile_detail.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        
        # Calculer l'ID du thread entre l'utilisateur connecté et le propriétaire du profil
        if user.is_authenticated and user != self.object.user:
            from apps.messaging.models import get_or_create_thread
            context['thread_id'] = get_or_create_thread(user, self.object.user).id
        else:
            context['thread_id'] = None # Pas de thread si on regarde son propre profil
            
        # 1. Récupérer toutes les images du profil
        context['profile_images'] = self.object.images.all()
        
        # 2. Récupérer spécifiquement l'image marquée comme couverture
        try:
            context['cover_image'] = self.object.images.get(is_cover=True)
        except ProfileImage.DoesNotExist:
            context['cover_image'] = None
            
        return context


# --- 3. ÉDITION DU PROFIL (CONNECTÉ SEULEMENT) ---
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "profiles/profile_edit.html"
    success_url = reverse_lazy('profiles:dashboard')
    form_class = ProfileForm

    def get_object(self):
        """Récupère le profil ou le crée si inexistant"""
        try:
            return self.request.user.profile
        except:
            # Création avec valeurs par défaut
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
        
        # Formulaire d'image de couverture
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
        form = ProfileForm(request.POST, request.FILES, instance=self.object)
        image_form = ProfileImageForm(request.POST, request.FILES)
        
        # Variables de succès
        profile_saved = False
        image_saved = False

        # 2. Validation et Sauvegarde du profil principal
        if form.is_valid():
            form.save()
            profile_saved = True
        else:
            # Si le formulaire principal est invalide, on retourne les erreurs
            return self.form_invalid(form)

        # 3. Validation et Sauvegarde de l'Image de couverture (Indépendante)
        if image_form.is_valid():
            image_form.save(self.object)
            image_saved = True

        # 4. Redirection
        if profile_saved:
            return HttpResponseRedirect(self.get_success_url())
        elif image_saved:
            return HttpResponseRedirect(request.path_info)
        else:
            return self.form_invalid(form)


# --- 4. DASHBOARD ---

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard dynamique avec vraies données :
    - Stats réelles (visites, likes, messages)
    - Complétude du profil calculée
    - Activité récente
    - Suggestions de profils
    """
    template_name = "profiles/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ===================================
        # 1. RÉCUPÉRER LE PROFIL
        # ===================================
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            # Si pas de profil, créer un profil minimal
            from datetime import date
            profile = Profile.objects.create(
                user=user,
                gender='M',
                city='Cotonou',
                country='Bénin',
                date_of_birth=date.today() - timedelta(days=18*365)
            )
        
        # ===================================
        # 2. CALCULER LA COMPLÉTUDE DU PROFIL
        # ===================================
        completion_steps = {
            'Informations de base': profile.gender and profile.date_of_birth and profile.city,
            'Photo de profil': profile.images.exists(),
            'Biographie': bool(profile.bio and len(profile.bio) > 20),
            'Objectif relationnel': bool(profile.relationship_goal),
            'Photo de couverture': profile.images.filter(is_cover=True).exists(),
        }
        
        completed_steps = sum(1 for completed in completion_steps.values() if completed)
        total_steps = len(completion_steps)
        completion = int((completed_steps / total_steps) * 100)
        
        # ===================================
        # 3. STATS RÉELLES
        # ===================================
        
        # A. Visites de profil (depuis ProfileView)
        try:
            # Visites cette semaine
            visits_count = ProfileView.objects.filter(
                viewed_profile=profile,
                viewed_at__gte=timezone.now() - timedelta(days=7)
            ).count()
        except:
            visits_count = 0
        
        # B. Messages non lus (depuis le modèle Message)
        try:
            from apps.messaging.models import Message, Thread
            
            unread_messages = Message.objects.filter(
                thread__participants=user,
                is_read=False
            ).exclude(sender=user).count()
            
            # Total de conversations actives
            active_conversations = Thread.objects.filter(
                participants=user,
                is_active=True
            ).count()
        except:
            unread_messages = 0
            active_conversations = 0
        
        # C. Statistiques basées sur les profils
        # Nombre de vues uniques (visiteurs différents)
        try:
            unique_visitors = ProfileView.objects.filter(
                viewed_profile=profile,
                viewed_at__gte=timezone.now() - timedelta(days=7)
            ).values('viewer').distinct().count()
        except:
            unique_visitors = 0
        
        stats = {
            'visits': visits_count,
            'unique_visitors': unique_visitors,
            'new_messages': unread_messages,
            'conversations': active_conversations,
        }
        
        # ===================================
        # 4. ACTIVITÉ RÉCENTE
        # ===================================
        recent_activities = []
        
        # A. Derniers likes reçus
        try:
            from apps.profiles.models import Like
            recent_likes = Like.objects.filter(
                liked_user=user
            ).select_related('user', 'user__profile').order_by('-created_at')[:5]
            
            for like in recent_likes:
                recent_activities.append({
                    'type': 'like',
                    'user': like.user,
                    'profile': like.user.profile if hasattr(like.user, 'profile') else None,
                    'timestamp': like.created_at,
                    'icon': 'heart',
                })
        except:
            pass
        
        # B. Derniers messages reçus
        try:
            from apps.messaging.models import Message
            recent_messages = Message.objects.filter(
                thread__participants=user
            ).exclude(
                sender=user
            ).select_related('sender', 'sender__profile', 'thread').order_by('-created_at')[:5]
            
            for message in recent_messages:
                recent_activities.append({
                    'type': 'message',
                    'user': message.sender,
                    'profile': message.sender.profile if hasattr(message.sender, 'profile') else None,
                    'timestamp': message.created_at,
                    'content': message.content[:50] if message.content else "Photo",
                    'thread_id': message.thread.id,
                    'icon': 'chat',
                })
        except:
            pass
        
        # Trier par date (plus récent en premier)
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]  # Garder les 10 plus récents
        
        # ===================================
        # 5. SUGGESTIONS DE PROFILS COMPATIBLES
        # ===================================
        suggested_profiles = []
        
        if profile:
            # Trouver des profils compatibles
            # Critères : même ville ou même pays, genre opposé (pour hétéro)
            suggested_profiles = Profile.objects.filter(
                is_active=True,
            ).exclude(
                user=user  # Pas moi-même
            ).select_related('user').prefetch_related('images')
            
            # Filtrer par genre opposé (si hétéro)
            if profile.gender == 'M':
                suggested_profiles = suggested_profiles.filter(gender='F')
            else:
                suggested_profiles = suggested_profiles.filter(gender='M')
            
            # Priorité 1 : Même ville
            same_city = suggested_profiles.filter(city=profile.city)[:3]
            
            # Priorité 2 : Même pays mais ville différente
            same_country = suggested_profiles.filter(
                country=profile.country
            ).exclude(city=profile.city)[:3]
            
            # Priorité 3 : Diaspora (si je suis diaspora)
            if profile.is_diaspora:
                diaspora = suggested_profiles.filter(is_diaspora=True)[:3]
                suggested_profiles = list(same_city) + list(diaspora) + list(same_country)
            else:
                suggested_profiles = list(same_city) + list(same_country)
            
            # Limiter à 6 suggestions
            suggested_profiles = suggested_profiles[:6]
        
        # ===================================
        # 6. POPULARITÉ DU PROFIL
        # ===================================
        # Score basé sur : photos, bio, likes reçus
        # On définit d'abord total_likes en comptant les objets Like
        try:
            from apps.profiles.models import Like
            total_likes = Like.objects.filter(liked_user=user).count()
        except ImportError:
            # Si le modèle Like n'est pas encore créé ou accessible
            total_likes = 0
        except Exception:
            total_likes = 0

        # Score basé sur : photos, bio, likes reçus
        popularity_score = 0
        if profile.images.count() > 0: popularity_score += 25
        if profile.images.count() >= 3: popularity_score += 15
        if profile.bio and len(profile.bio) > 50: popularity_score += 20
        
        # Maintenant total_likes est défini et peut être utilisé
        if total_likes > 0: 
            popularity_score += min(40, total_likes * 2)
        
        popularity_level = 'Débutant'
        if popularity_score >= 80:
            popularity_level = 'Star ⭐'
        elif popularity_score >= 60:
            popularity_level = 'Populaire 🔥'
        elif popularity_score >= 40:
            popularity_level = 'En hausse 📈'
        
        # ===================================
        # 7. AJOUTER AU CONTEXTE
        # ===================================
        context.update({
            'profile': profile,
            'completion': completion,
            'completion_steps': completion_steps,
            'stats': stats,
            'recent_activities': recent_activities,
            'suggested_profiles': suggested_profiles,
            'popularity_score': popularity_score,
            'popularity_level': popularity_level,
        })
        
        return context

#htmx----------------------------------------zone--------------------
from django.http import HttpResponse
from django.shortcuts import render

def upload_cover(request):
    """
    Vue HTMX pour upload la couverture instantanément.
    """
    if not request.user.is_authenticated:
        return HttpResponse("Non autorisé", status=401)
    
    try:
        profile = request.user.profile
    except:
        return HttpResponse("Profil introuvable", status=404)

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save(profile)
            # Récupérer la nouvelle couverture
            cover = profile.images.get(is_cover=True)
            
            # CORRECTION DU PATH : On pointe vers le template dans 'profiles/partials'
            return render(request, 'profiles/partials/cover_display.html', {'cover': cover})
            
    # Si pas POST, retourner le bloc actuel (GET)
    try:
        cover = profile.images.get(is_cover=True)
    except Profile.DoesNotExist:
        cover = None
        
    # CORRECTION DU PATH
    return render(request, 'profiles/partials/cover_display.html', {'cover': cover})