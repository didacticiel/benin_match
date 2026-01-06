# apps/messaging/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView
from django.http import HttpResponse
from django.db.models import Q, Max, Count, Prefetch
from django.urls import reverse_lazy

from .models import Thread, Message, get_or_create_thread
from .forms import MessageForm


# ===================================
# 1. INBOX - Liste des conversations
# ===================================
class InboxView(LoginRequiredMixin, ListView):
    """
    Affiche la liste de toutes les conversations de l'utilisateur connecté.
    
    LOGIQUE DE CORRECTION :
    L'erreur "Cannot filter a query once a slice has been taken" arrivait car 
    nous essayions de faire un .count() sur un QuerySet de messages déjà limité 
    par un slice [:1]. 
    
    SOLUTION :
    1. Utiliser 'to_attr' dans le Prefetch pour isoler le dernier message.
    2. Recalculer le compteur de messages non lus de manière indépendante.
    """
    template_name = "messaging/inbox.html"
    context_object_name = 'thread_list'
    paginate_by = 20

    def get_queryset(self):
        """
        REQUÊTE OPTIMISÉE pour récupérer les conversations.
        
        ÉTAPES & OPTIMISATIONS :
        - filter : On cible uniquement les conversations actives de l'utilisateur.
        - prefetch_related + to_attr : On récupère les messages classés par date, 
          mais on les stocke dans un attribut virtuel 'prefetched_messages' pour 
          ne pas interférer avec le manager .messages par défaut.
        - annotate : On récupère la date du message le plus récent pour le tri global.
        """
        user = self.request.user
        
        # On définit le queryset de messages pour le prefetch (plus récent d'abord)
        messages_qs = Message.objects.select_related('sender').order_by('-created_at')

        return Thread.objects.filter(
            participants=user,
            is_active=True
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=messages_qs,
                to_attr='prefetched_messages'  # Crucial pour éviter l'erreur de slicing
            )
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')

    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte en calculant les métadonnées de chaque thread.
        
        DÉTAILS DES CALCULS :
        1. Identification de l'interlocuteur : On extrait le participant qui n'est pas l'utilisateur actuel.
        2. Comptage sécurisé : On effectue un .filter().count() sur le modèle Message 
           pour éviter de toucher au QuerySet pré-chargé (évite l'erreur TypeError).
        3. Extraction du dernier message : On pioche simplement le premier élément 
           de notre liste 'prefetched_messages'.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        thread_data = []
        total_unread = 0
        
        # Parcourir les threads récupérés par la pagination
        for thread in context['thread_list']:
            # Récupérer l'autre utilisateur via la méthode du modèle
            other_user = thread.get_other_participant(user)
            
            if not other_user:
                continue

            # SÉCURITÉ & CORRECTION : 
            # On compte les messages non lus en repartant du modèle Message.
            # Cela évite d'appliquer un filtre sur un QuerySet déjà tranché (sliced).
            unread_count = Message.objects.filter(
                thread=thread,
                is_read=False
            ).exclude(sender=user).count()
            
            total_unread += unread_count
            
            # Récupérer le dernier message depuis l'attribut pré-chargé (to_attr)
            # Puisque le queryset était trié par '-created_at', l'index 0 est le plus récent.
            last_msg = None
            if hasattr(thread, 'prefetched_messages') and thread.prefetched_messages:
                last_msg = thread.prefetched_messages[0]
            
            # On construit notre dictionnaire de données pour le template
            thread_data.append({
                'thread': thread,
                'other_user': other_user,
                'unread_count': unread_count,
                'last_message': last_msg,
            })
        
        # Ajout des variables au contexte final
        context['threads'] = thread_data
        context['total_unread'] = total_unread
        
        return context

# ===================================
# 2. CHAT - Page de conversation
# ===================================
class ChatView(LoginRequiredMixin, View):
    """
    Affiche la page de chat avec un utilisateur.
    
    FONCTIONNALITÉS :
    - GET : Affiche les messages existants
    - POST : Envoie un nouveau message (avec HTMX)
    
    SÉCURITÉ :
    - Vérifie que l'utilisateur est bien participant à la conversation
    """
    template_name = "messaging/chat.html"

    def get_object(self):
        """
        Récupère le Thread et vérifie la sécurité.
        
        IMPORTANT : On vérifie que l'utilisateur connecté est bien
        participant de cette conversation, sinon on redirige.
        """
        thread = get_object_or_404(Thread, id=self.kwargs['pk'])
        user = self.request.user
        
        # SÉCURITÉ : Est-ce que je fais partie de cette conversation ?
        if user not in thread.participants.all():
            # Non autorisé : rediriger vers la liste des profils
            return None
        
        return thread

    def get(self, request, *args, **kwargs):
        """
        Affiche la page de chat (requête GET).
        
        ÉTAPES :
        1. Récupérer le thread et vérifier la sécurité
        2. Charger les messages (optimisé avec select_related)
        3. Marquer les messages de l'autre comme LUS
        4. Préparer le contexte pour le template
        """
        thread = self.get_object()
        
        # Si pas autorisé, rediriger
        if not thread:
            return redirect('profiles:list')
        
        user = request.user

        # OPTIMISATION : Charger les messages avec leur sender en 1 requête
        # On limite à 50 messages pour ne pas surcharger
        messages = thread.messages.select_related('sender').order_by('created_at')[:50]
        
        # FONCTIONNALITÉ : Marquer les messages de l'AUTRE comme lus
        # Explication : Quand j'ouvre la conversation, je lis tout
        thread.messages.filter(
            is_read=False           # Seulement les non lus
        ).exclude(
            sender=user             # Sauf mes propres messages
        ).update(is_read=True)      # Marquer comme lus

        # Récupérer l'autre participant
        other_user = thread.get_other_participant(user)

        # Préparer le formulaire d'envoi
        form = MessageForm()

        # ID du dernier message (pour le polling JavaScript)
        # CORRECTION : On convertit en liste pour pouvoir accéder au dernier élément
        messages_list = list(messages)
        last_message_id = messages_list[-1].id if messages_list else 0

        # Renvoyer le template avec toutes les données
        return render(request, self.template_name, {
            'thread': thread,
            'messages': messages_list,  # On passe la liste au lieu du QuerySet
            'form': form,
            'other_user': other_user,
            'last_message_id': last_message_id  # Important pour le polling
        })

    def post(self, request, *args, **kwargs):
        """
        Envoie un nouveau message (requête POST avec HTMX).
        
        HTMX : Au lieu de recharger toute la page, on renvoie
        SEULEMENT le HTML du nouveau message qui sera inséré dynamiquement.
        
        LOGIQUE :
        1. Valider le formulaire
        2. Créer le message en base de données
        3. Renvoyer le HTML du message (partial template)
        """
        thread = self.get_object()
        
        if not thread:
            return redirect('profiles:list')
        
        user = request.user

        # Récupérer et valider les données du formulaire
        form = MessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Créer le message en base de données
            message = Message.objects.create(
                thread=thread,
                sender=user,
                content=form.cleaned_data['content'],
                image=form.cleaned_data.get('image')
            )
            
            # Si la requête vient de HTMX (requête AJAX)
            if request.headers.get('HX-Request'):
                # Renvoyer SEULEMENT le HTML du nouveau message
                # Ce HTML sera inséré automatiquement par HTMX
                return render(request, 'messaging/partials/single_message.html', {
                    'message': message,
                    'user': user  # Pour savoir si c'est mon message
                })
            else:
                # Fallback : Si pas HTMX, recharger la page normalement
                return redirect(request.path_info)
        
        # Si le formulaire est invalide
        if request.headers.get('HX-Request'):
            # Renvoyer les erreurs pour HTMX
            return render(request, 'messaging/partials/form_errors.html', {
                'form': form
            })
        else:
            # Recharger la page avec les erreurs
            return self.get(request, *args, **kwargs)


# ===================================
# 3. POLLING - Récupérer nouveaux messages
# ===================================
class NewMessagesView(LoginRequiredMixin, View):
    """
    API de Polling : Cette vue est appelée par JavaScript toutes les 3 secondes.
    
    PRINCIPE DU POLLING :
    - Le JavaScript envoie l'ID du dernier message qu'il a
    - On cherche les messages PLUS RÉCENTS que cet ID
    - On renvoie le HTML de ces nouveaux messages
    - Le JavaScript les insère dans la page
    
    C'est ainsi qu'on simule le "temps réel" sans WebSocket.
    """
    
    def get(self, request, pk):
        """
        Récupère les nouveaux messages depuis un certain ID.
        
        PARAMÈTRES :
        - pk : ID du thread
        - last_id (GET) : ID du dernier message reçu par le client
        
        RETOUR :
        - HTML des nouveaux messages (ou vide s'il n'y en a pas)
        """
        # Récupérer l'ID du dernier message connu par le client
        last_id = int(request.GET.get('last_id', 0))
        
        # Récupérer le thread
        thread = get_object_or_404(Thread, id=pk)
        user = request.user
        
        # SÉCURITÉ : Vérifier que je suis participant
        if user not in thread.participants.all():
            return HttpResponse("Interdit", status=403)

        # REQUÊTE : Chercher les messages PLUS RÉCENTS que last_id
        # IMPORTANT : On exclut ses propres messages pour éviter les doublons
        # (car j'ai déjà mes messages affichés via HTMX)
        new_messages = thread.messages.filter(
            id__gt=last_id              # ID supérieur à last_id (plus récent)
        ).exclude(
            sender=user                 # Pas mes propres messages
        ).select_related('sender')      # Optimisation : charger le sender

        # Si aucun nouveau message, renvoyer vide
        if not new_messages.exists():
            return HttpResponse("")  # Vide = rien de nouveau

        # MARQUER LES NOUVEAUX MESSAGES COMME LUS
        new_messages.update(is_read=True)

        # Renvoyer le HTML des nouveaux messages
        return render(request, 'messaging/partials/new_messages_list.html', {
            'messages': new_messages,
            'user': user
        })


# ===================================
# 4. DÉMARRER UNE CONVERSATION
# ===================================
def start_conversation(request, user_id):
    """
    Crée ou récupère une conversation avec un utilisateur.
    
    USAGE : Depuis un profil, cliquer sur "Envoyer un message"
    
    LOGIQUE :
    1. Vérifier que l'utilisateur existe
    2. Créer ou récupérer le thread entre les 2 utilisateurs
    3. Rediriger vers la page de chat
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.decorators import login_required
    
    User = get_user_model()
    
    # Récupérer l'autre utilisateur
    other_user = get_object_or_404(User, id=user_id)
    
    # Ne pas créer de conversation avec soi-même
    if other_user == request.user:
        return redirect('messaging:list')
    
    # Créer ou récupérer le thread
    thread = get_or_create_thread(request.user, other_user)
    
    # Rediriger vers la page de chat
    return redirect('messaging:detail', pk=thread.id)