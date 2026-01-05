# apps/payments/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Transaction(models.Model):
    """Historique de toutes les transactions"""
    
    TRANSACTION_STATUS = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('declined', 'Refusé'),
        ('canceled', 'Annulé'),
    ]
    
    TRANSACTION_TYPE = [
        ('premium_subscription', 'Abonnement Premium'),
        ('one_time_download', 'Téléchargement Unique'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    cv = models.ForeignKey('cv_app.CV', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Informations FedaPay
    fedapay_transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    fedapay_token = models.CharField(max_length=255, blank=True)
    
    # Détails transaction
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    
    # Métadonnées
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_transaction_type_display()} - {self.amount} {self.currency}"


class PremiumSubscription(models.Model):
    """Gestion des abonnements Premium"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Abonnement Premium'
        verbose_name_plural = 'Abonnements Premium'
    
    def __str__(self):
        return f"{self.user.email} - Premium jusqu'au {self.end_date.date()}"
    
    def is_valid(self):
        """Vérifie si l'abonnement est toujours valide"""
        return self.is_active and self.end_date > timezone.now()
    
    def activate_subscription(self, duration_days=30):
        """Active l'abonnement pour une durée donnée"""
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=duration_days)
        self.is_active = True
        self.save()
        
        # Mettre à jour le statut premium de l'utilisateur
        self.user.is_premium_subscriber = True
        self.user.save()


class DownloadCredit(models.Model):
    """Crédits de téléchargement unique"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_credits_log')
    cv = models.ForeignKey('cv_app.CV', on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True)
    
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Crédit de Téléchargement'
        verbose_name_plural = 'Crédits de Téléchargement'
    
    def __str__(self):
        return f"{self.user.email} - CV: {self.cv.title if self.cv else 'N/A'} - {'Utilisé' if self.is_used else 'Disponible'}"
    
    def use_credit(self):
        """Marque le crédit comme utilisé"""
        if not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save()
            return True
        return False
