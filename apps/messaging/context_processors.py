# apps/messaging/context_processors.py
from .models import Message

def unread_messages_count(request):
    if request.user.is_authenticated:
        # On compte les messages où l'utilisateur est destinataire et is_read=False
        # Adapte la requête selon ton modèle exact (ex: thread__participants=request.user)
        count = Message.objects.filter(
            thread__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_count': count}
    return {'unread_count': 0}