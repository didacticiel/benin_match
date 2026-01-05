# apps/payments/urls.py - CORRIGÉ

from django.urls import path
from .views import (
    CreateTransactionView,
    # 🛑 Correction de 'CanDownloadView' à 'CheckDownloadPermissionView'
    CheckDownloadPermissionView, 
    # 🛑 Correction de 'ConsumeCreditsView' à 'ConsumeDownloadCreditView'
    ConsumeDownloadCreditView,
    CheckTransactionStatusView,
    fedapay_callback,
    FedaPayWebhookView # Ajoutez FedaPayWebhookView si vous l'utilisez
)

app_name = 'payments'

urlpatterns = [
    # Endpoints API
    path('create-transaction/', CreateTransactionView.as_view(), name='create_transaction'),
    
    #  Mise à jour du nom de la vue et de l'URL pour la clarté
    path('can-download/<int:cv_id>/', CheckDownloadPermissionView.as_view(), name='can_download'),
    
    # Mise à jour du nom de la vue
    path('consume-credit/', ConsumeDownloadCreditView.as_view(), name='consume_credit'),
    
    path('check-status/<int:transaction_id>/', CheckTransactionStatusView.as_view(), name='check_status'),
    
    # Callback FedaPay (Redirection utilisateur)
    path('callback/', fedapay_callback, name='fedapay_callback'),
    
    #  Webhook FedaPay (Appel serveur à serveur)
    path('webhook/', FedaPayWebhookView.as_view(), name='fedapay_webhook'), 
]