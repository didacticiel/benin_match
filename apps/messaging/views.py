# apps/messaging/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Max, Count, Prefetch
from django.urls import reverse_lazy
from django.core.files.storage import default_storage

from .models import Thread, Message, get_or_create_thread
from .forms import MessageForm


# ===================================
# 1. INBOX - Liste des conversations
# ===================================
class InboxView(LoginRequiredMixin, ListView):
    template_name = "messaging/inbox.html"
    context_object_name = 'thread_list'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        
        messages_qs = Message.objects.select_related('sender').order_by('-created_at')

        return Thread.objects.filter(
            participants=user,
            is_active=True
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=messages_qs,
                to_attr='prefetched_messages'
            )
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        thread_data = []
        total_unread = 0
        
        for thread in context['thread_list']:
            other_user = thread.get_other_participant(user)
            
            if not other_user:
                continue

            # Compter les messages non lus
            unread_count = Message.objects.filter(
                thread=thread,
                is_read=False
            ).exclude(sender=user).count()
            
            total_unread += unread_count
            
            # Récupérer le dernier message
            last_msg = None
            if hasattr(thread, 'prefetched_messages') and thread.prefetched_messages:
                last_msg = thread.prefetched_messages[0]
            
            thread_data.append({
                'thread': thread,
                'other_user': other_user,
                'unread_count': unread_count,
                'last_message': last_msg,
            })
        
        context['threads'] = thread_data
        context['total_unread'] = total_unread
        
        return context


# ===================================
# 2. CHAT - Page de conversation (CORRIGÉ)
# ===================================
class ChatView(LoginRequiredMixin, View):
    template_name = "messaging/chat.html"

    def get_object(self):
        thread = get_object_or_404(Thread, id=self.kwargs['pk'])
        user = self.request.user
        
        if user not in thread.participants.all():
            return None
        
        return thread

    def get(self, request, *args, **kwargs):
        thread = self.get_object()
        
        if not thread:
            return redirect('profiles:list')
        
        user = request.user

        # Charger les 50 derniers messages
        messages = thread.messages.select_related('sender').order_by('-created_at')[:50]
        
        # Inverser l'ordre pour l'affichage (du plus ancien au plus récent)
        messages_list = list(reversed(messages))
        
        # Marquer les messages de l'autre comme lus
        thread.messages.filter(
            is_read=False
        ).exclude(
            sender=user
        ).update(is_read=True)

        # Récupérer l'autre participant
        other_user = thread.get_other_participant(user)

        # Préparer le formulaire
        form = MessageForm()

        # ID du dernier message pour le polling
        last_message_id = messages[0].id if messages else 0

        return render(request, self.template_name, {
            'thread': thread,
            'messages': messages_list,
            'form': form,
            'other_user': other_user,
            'last_message_id': last_message_id
        })

    def post(self, request, *args, **kwargs):
        thread = self.get_object()
        
        if not thread:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        user = request.user

        # Créer le formulaire avec les données
        form = MessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Créer le message
            message = Message.objects.create(
                thread=thread,
                sender=user,
                content=form.cleaned_data['content'],
                image=form.cleaned_data.get('image')
            )
            
            # Réponse JSON pour HTMX avec toutes les informations nécessaires
            if request.headers.get('HX-Request'):
                return render(request, 'messaging/partials/single_message.html', {
                    'message': message,
                    'user': user
                })
            else:
                return redirect(request.path_info)
        else:
            # Si le formulaire est invalide
            if request.headers.get('HX-Request'):
                return HttpResponse('<div class="text-red-500 p-2">Erreur lors de l\'envoi du message</div>', status=400)
            else:
                return self.get(request, *args, **kwargs)


# ===================================
# 3. POLLING - CORRIGÉ pour affichage temps réel
# ===================================
class NewMessagesView(LoginRequiredMixin, View):
    """
    Vue corrigée pour le polling.
    Retourne les nouveaux messages depuis le dernier ID connu.
    """
    
    def get(self, request, pk):
        # Récupérer l'ID du dernier message connu
        last_id = int(request.GET.get('last_id', 0))
        
        # Récupérer le thread
        thread = get_object_or_404(Thread, id=pk)
        user = request.user
        
        # Vérifier la sécurité
        if user not in thread.participants.all():
            return HttpResponse("Unauthorized", status=403)

        # Récupérer les nouveaux messages (plus récents que last_id)
        new_messages = thread.messages.filter(
            id__gt=last_id
        ).exclude(
            sender=user  # Exclure ses propres messages
        ).select_related('sender').order_by('created_at')
        
        # Si pas de nouveaux messages, retourner une réponse vide
        if not new_messages.exists():
            return HttpResponse("", status=200)

        # Marquer comme lus
        new_messages.update(is_read=True)
        
        # Mettre à jour le dernier ID
        last_message_id = new_messages.last().id
        
        # Renvoyer le HTML des nouveaux messages
        return render(request, 'messaging/partials/new_messages_list.html', {
            'messages': new_messages,
            'user': user,
            'last_message_id': last_message_id
        })


# ===================================
# 4. VUE POUR VÉRIFIER LES NOUVEAUX MESSAGES (API JSON)
# ===================================
class CheckNewMessagesView(LoginRequiredMixin, View):
    """
    Vue API qui retourne les nouveaux messages en JSON.
    Utile pour le JavaScript.
    """
    
    def get(self, request, pk):
        last_id = int(request.GET.get('last_id', 0))
        
        thread = get_object_or_404(Thread, id=pk)
        user = request.user
        
        if user not in thread.participants.all():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Récupérer les nouveaux messages
        new_messages = thread.messages.filter(
            id__gt=last_id
        ).exclude(
            sender=user
        ).select_related('sender').order_by('created_at')
        
        # Sérialiser les messages
        messages_data = []
        for msg in new_messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'image_url': msg.image.url if msg.image else None,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.get_full_name(),
                'sender_avatar': msg.sender.avatar.url if msg.sender.avatar else None,
                'created_at': msg.created_at.strftime('%H:%M'),
                'is_mine': msg.sender == user
            })
        
        # Marquer comme lus
        new_messages.update(is_read=True)
        
        # Dernier ID
        last_message_id = new_messages.last().id if new_messages.exists() else last_id
        
        return JsonResponse({
            'has_new': new_messages.exists(),
            'messages': messages_data,
            'last_message_id': last_message_id
        })


# ===================================
# 5. DÉMARRER UNE CONVERSATION
# ===================================
def start_conversation(request, user_id):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.decorators import login_required
    
    User = get_user_model()
    
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        return redirect('messaging:list')
    
    thread = get_or_create_thread(request.user, other_user)
    
    return redirect('messaging:detail', pk=thread.id)