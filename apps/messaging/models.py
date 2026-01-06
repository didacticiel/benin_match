from django.db import models
from django.db.models import Count  # Importation corrigée
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Thread(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='threads')
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"

    def __str__(self):
        return f"Thread {self.id}"

    def get_other_participant(self, user):
        """Retourne l'autre participant (méthode corrigée)"""
        return self.participants.exclude(id=user.id).first()

    @property
    def last_message(self):
        return self.messages.first()


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(verbose_name="Message")
    image = models.ImageField(upload_to="message_images/", blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message"
    
    def __str__(self):
        return f"Message de {self.sender.email}"


def get_or_create_thread(user1, user2):
    """Trouve ou crée une conversation entre user1 et user2"""
    thread = user1.threads.annotate(
        user_count=Count('participants')
    ).filter(user_count=2, participants=user2).first()

    if not thread:
        thread = Thread.objects.create()
        thread.participants.add(user1, user2)
    
    return thread