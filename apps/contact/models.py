from django.db import models

class ContactMessage(models.Model):
    """
    Stocke les messages envoyés via le formulaire de contact.
    """
    full_name = models.CharField(max_length=100, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_read = models.BooleanField(default=False, verbose_name="Lu par l'admin")

    class Meta:
        verbose_name = "Message de contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.subject}"