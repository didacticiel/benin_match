# =====================================================================
# FICHIER PRINCIPAL DES VUES DE PAIEMENT (CORRIGÉ ET FINALISÉ)
# =====================================================================

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
from django.shortcuts import redirect

from .models import Transaction, PremiumSubscription, DownloadCredit
from apps.cv_app.models import CV

import hmac
import hashlib
import json
import logging

try:
    import fedapay
except ImportError:
    fedapay = None

logger = logging.getLogger(__name__)


def get_payment_session():
    """Crée une session requests configurée pour les API de paiement"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# =====================================================================
# 🛠️ FONCTION UTILITAIRE : Interrogation FedaPay par HTTP
# =====================================================================
def get_fedapay_transaction_status(fedapay_id: str) -> str:
    """Interroge l'API FedaPay pour obtenir le statut d'une transaction via HTTP."""
    fedapay_url = f"{settings.FEDAPAY_API_URL}/transactions/{fedapay_id}"
    session = get_payment_session()
    
    headers = {
        'Authorization': f'Bearer {settings.FEDAPAY_SECRET_KEY}',
        'Accept': 'application/json',
    }
    
    try:
        response = session.get(fedapay_url, headers=headers, timeout=10)
        response.raise_for_status() 
        
        fedapay_data = response.json()
        transaction_data = fedapay_data.get('v1/transaction') or fedapay_data.get('transaction') or fedapay_data
        
        status_feda = transaction_data.get('status')
        if not status_feda:
            raise Exception("Statut FedaPay introuvable dans la réponse.")
            
        return status_feda
        
    except requests.exceptions.RequestException as e:
        logger.error(f" Erreur réseau/API FedaPay lors de la récupération: {str(e)}")
        raise


# =====================================================================
# 🔵 1️⃣ CREATION D’UNE TRANSACTION (LOGIQUE DE REDIRECTION RETABLIE)
# =====================================================================
class CreateTransactionView(APIView):
    """Crée une transaction via l'API REST FedaPay avec le format confirmé."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        transaction_type = request.data.get('transaction_type')
        cv_id = request.data.get('cv_id')
        
        # 1. Définition du Montant et de la Description
        cv = None
        amount = 0
        
        if transaction_type == 'premium_subscription':
            amount = 5000
            description = f"Abonnement Premium - 1 mois - {user.email}"
        elif transaction_type == 'one_time_download':
            if not cv_id:
                return Response(
                    {'error': 'ID du CV requis pour le téléchargement unique'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                cv = CV.objects.get(id=cv_id, owner=user) 
            except CV.DoesNotExist:
                return Response(
                    {'error': 'CV introuvable ou non possédé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            amount = 200
            description = f"Téléchargement CV: {cv.title} - {user.email}"
        else:
            return Response(
                {'error': 'Type de transaction invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if amount <= 0:
            return Response({'error': 'Montant invalide'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Préparation de la Requête FedaPay
        reference_id = f'CV{user.id}_{int(timezone.now().timestamp())}'
        session = get_payment_session()
        fedapay_url = f"{settings.FEDAPAY_API_URL}/transactions"
        
        # ✅ CLÉ DE LA CORRECTION : Utiliser l'URL du Front-end comme callback_url 
        # FedaPay ajoutera les paramètres ?transaction_id=FEDAPAY_ID&status=...
        frontend_success_url = f"{settings.FRONTEND_URL}/payment/success"
        webhook_url = f"{settings.BACKEND_DOMAIN}/api/v1/payments/webhook/"
        
        payload = {
            "description": description,
            "amount": amount,
            "currency": {
                "iso": "XOF"
            },
            "callback_url": frontend_success_url,  # ✅ Redirection directe vers le Front-end
            "webhook_url": webhook_url,  
            "reference": reference_id, 
            "customer": {
                "firstname": user.first_name or "Utilisateur",
                "lastname": user.last_name or "CV",
                "email": user.email,
                "phone_number": {
                    "number": request.data.get("phone_number", "+22967796730"),
                    "country": request.data.get("phone_country", "bj")
                }
            }
        }
        
        headers = {
            'Authorization': f'Bearer {settings.FEDAPAY_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        try:
            # 3. Envoi de la Requête
            response = session.post(
                fedapay_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            fedapay_data = response.json()

            # 4. Traitement de la Réponse
            if response.status_code in [200, 201]:
                
                transaction_data = fedapay_data.get('v1/transaction') or fedapay_data.get('transaction') or fedapay_data
                
                fedapay_transaction_id = transaction_data.get('id')
                fedapay_token = transaction_data.get('payment_token')
                payment_url = transaction_data.get('payment_url')
                
                if not all([fedapay_transaction_id, payment_url]):
                    logger.error(f"❌ Données critiques FedaPay manquantes (id={fedapay_transaction_id}, url={payment_url})")
                    raise Exception("La réponse FedaPay est incomplète.")
                
                # 5. Enregistrement en DB
                with db_transaction.atomic():
                    transaction_obj = Transaction.objects.create(
                        user=user,
                        cv=cv,
                        fedapay_transaction_id=fedapay_transaction_id,
                        fedapay_token=fedapay_token or 'N/A',
                        transaction_type=transaction_type,
                        amount=amount,
                        currency='XOF',
                        description=description,
                        status='pending',
                        metadata={
                            'fedapay_response': fedapay_data,
                            'cv_id': cv_id,
                            'cv_title': cv.title if cv else None
                        }
                    )
                
                logger.info(f"✅ Transaction FedaPay créée: {transaction_obj.id}. URL de paiement: {payment_url}")
                
                return Response({
                    'success': True,
                    'transaction_id': transaction_obj.id, # C'est l'ID local, utilisé pour CheckStatus plus tard
                    'fedapay_token': fedapay_token,
                    'payment_url': payment_url, # 🛑 C'est cette URL que le Front-end doit utiliser pour rediriger l'utilisateur vers FedaPay
                }, status=status.HTTP_201_CREATED)
            
            else:
                error_message = fedapay_data.get('message') or fedapay_data.get('error') or response.text
                logger.error(f"❌ Erreur FedaPay API ({response.status_code}): {error_message}")
                
                if response.status_code == 401:
                    detail = "Clé API FedaPay invalide. Vérifiez FEDAPAY_SECRET_KEY."
                else:
                    detail = f"Erreur externe: {error_message}"
                    
                return Response(
                    {'error': 'Erreur API FedaPay', 'detail': detail},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur réseau FedaPay: {str(e)}")
            return Response(
                {'error': 'Erreur réseau/Timeout vers FedaPay'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"❌ Erreur critique lors de la création de transaction: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Erreur serveur interne'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =====================================================================
# 🟢 2️⃣ CALLBACK FedaPay (Redirection vers le Front-end) (AJUSTÉ)
# =====================================================================
@api_view(['GET'])
@permission_classes([AllowAny])  
def fedapay_callback(request):
    """
    Endpoint appelé par FedaPay après le paiement (via callback_url).
    Redirige l'utilisateur vers la page Front-end pour la vérification finale.
    """
    fedapay_id = request.GET.get('transaction_id')
    status_code = request.GET.get('status')
    
    logger.info(f"🔔 Callback FedaPay reçu: fedapay_id={fedapay_id}, status={status_code}")
    
    frontend_url = settings.FRONTEND_URL or 'http://localhost:3000'
    local_id = None
    
    # 🛑 Récupérer l'ID local (Django) à partir de l'ID FedaPay
    if fedapay_id:
        try:
            transaction = Transaction.objects.get(fedapay_transaction_id=fedapay_id)
            local_id = transaction.id
        except Transaction.DoesNotExist:
            logger.error(f"Transaction locale introuvable pour ID FedaPay: {fedapay_id}")

    # Le Front-end a besoin de l'ID local (local_id) pour appeler CheckTransactionStatusView
    redirect_id = local_id or fedapay_id
    
    # Si nous n'avons même pas l'ID FedaPay, rediriger vers une page d'erreur générique
    if not redirect_id:
        redirect_url = f"{frontend_url}/payment/failed?status=missing_id"
        logger.error("🔗 Redirection vers échec: ID FedaPay manquant dans le callback.")
        return redirect(redirect_url)


    # Redirection vers la Page de Succès Front-end
    redirect_url = (
        f"{frontend_url}/payment/success"
        f"?transaction_id={redirect_id}" # Utilise l'ID local s'il existe, sinon l'ID FedaPay (le Front-end devra gérer l'ID FedaPay)
        f"&fedapay_status={status_code}" 
    )
    
    logger.info(f"🔗 Redirection vers le Front-end: {redirect_url}")
    return redirect(redirect_url)


# =====================================================================
# 🟡 3️⃣ VÉRIFICATION DU STATUT POST-REDIRECTION
# =====================================================================
class CheckTransactionStatusView(APIView):
    """
    Vérifie le statut d'une transaction via l'ID local (appelé par le Front-end).
    Effectue une vérification auprès de FedaPay si le statut est toujours 'pending'.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id): # transaction_id est l'ID local Django
        user = request.user
        
        try:
            # 1. Récupérer la transaction en base de données
            transaction = Transaction.objects.get(
                id=transaction_id,
                user=user
            )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction non trouvée ou non autorisée'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        fedapay_id = transaction.fedapay_transaction_id
        
        # 2. Si déjà approuvée en DB (via Webhook), retourner le statut immédiatement
        if transaction.status == 'approved':
            return Response({
                'status': 'approved',
                'cv_id': transaction.cv.id if transaction.cv else None,
                'transaction_type': transaction.transaction_type,
            })
        
        # 3. Sinon, vérifier auprès de FedaPay via requêtes HTTP
        try:
            fedapay_status = get_fedapay_transaction_status(fedapay_id) 
            
            if fedapay_status == 'approved':
                
                # LOGIQUE D'ACTIVATION (si le Webhook a été manqué)
                self._handle_approved_transaction(transaction) 
                
                logger.info(f"✅ Transaction {transaction_id} approuvée et accès accordé via CheckStatus")
                
                return Response({
                    'status': 'approved',
                    'cv_id': transaction.cv.id if transaction.cv else None,
                    'transaction_type': transaction.transaction_type,
                })
            
            elif fedapay_status in ['declined', 'canceled']:
                # Mettre à jour la DB si FedaPay a un statut final
                with db_transaction.atomic():
                    transaction.status = fedapay_status
                    transaction.save()
                    
                return Response({
                    'status': fedapay_status,
                    'cv_id': None,
                    'transaction_type': transaction.transaction_type,
                })
            
            else:
                # Statut 'pending' ou autre statut temporaire
                return Response({
                    'status': fedapay_status,
                    'cv_id': None,
                    'transaction_type': transaction.transaction_type,
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification FedaPay pour {fedapay_id}: {str(e)}", exc_info=True)
            # Retourner une erreur serveur et le statut 'pending'
            return Response(
                {'error': 'Erreur serveur lors de la vérification externe', 'status': 'pending'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @db_transaction.atomic
    def _handle_approved_transaction(self, transaction_obj):
        """Logique d'activation manuelle, copiée de la méthode du Webhook pour la résilience."""
        
        if transaction_obj.status == 'approved':
            logger.warning(f" Transaction {transaction_obj.id} déjà approuvée. Ignoré.")
            return

        transaction_obj.status = 'approved'
        transaction_obj.approved_at = timezone.now()
        transaction_obj.save()
        
        user = transaction_obj.user
        
        # CAS 1: PREMIUM
        if transaction_obj.transaction_type == 'premium_subscription':
            subscription, created = PremiumSubscription.objects.get_or_create(user=user)
            subscription.transaction = transaction_obj
            subscription.activate_subscription(duration_days=30)
            
            user.is_premium_subscriber = True 
            user.save()
            
        
        # CAS 2: TÉLÉCHARGEMENT UNIQUE
        elif transaction_obj.transaction_type == 'one_time_download':
            DownloadCredit.objects.get_or_create(
                user=user,
                cv=transaction_obj.cv,
                transaction=transaction_obj,
                defaults={'is_used': False}
            )
            user.download_credits = (user.download_credits or 0) + 1
            user.save()


# =====================================================================
# 🔴 4️⃣ WEBHOOK FedaPay — APPROBATION & ÉCHEC
# =====================================================================
class FedaPayWebhookView(APIView):
    """Gère l'appel serveur-serveur de FedaPay (Webhook) pour validation."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # 1. Vérifier la signature (IMPORTANT POUR LA SÉCURITÉ)
        signature = request.headers.get('X-FedaPay-Signature')
        
        if settings.DEBUG and not signature:
            logger.warning(" MODE DEBUG: Vérification signature ignorée.")
        elif not self._verify_signature(request.body, signature):
            logger.warning("Signature webhook invalide")
            return Response(
                {'error': 'Signature invalide'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. Parser les données et gérer l'événement
        try:
            event_data = request.data
            transaction_data = event_data.get('entity', {})
            fedapay_transaction_id = transaction_data.get('id')
            
            if not fedapay_transaction_id:
                logger.error(" ID transaction FedaPay manquant dans le Webhook.")
                return Response({'error': 'ID transaction manquant'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 3. Récupérer notre transaction
            try:
                transaction_obj = Transaction.objects.get(fedapay_transaction_id=fedapay_transaction_id)
            except Transaction.DoesNotExist:
                logger.error(f" Transaction DB introuvable pour ID FedaPay: {fedapay_transaction_id}")
                return Response({'error': 'Transaction introuvable'}, status=status.HTTP_404_NOT_FOUND)
            
            # 4. Traiter selon le statut FedaPay
            status_feda = transaction_data.get('status')
            
            if status_feda == 'approved':
                self._handle_approved_transaction(transaction_obj)
            
            elif status_feda in ['declined', 'canceled']:
                transaction_obj.status = status_feda
                transaction_obj.save()
                logger.info(f" Transaction {status_feda}: {transaction_obj.id}")
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f" Erreur webhook: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Erreur serveur'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _verify_signature(self, payload, signature):
        """Vérifie la signature HMAC du Webhook."""
        if not signature:
            return False
        
        webhook_secret = getattr(settings, 'FEDAPAY_WEBHOOK_SECRET', '')
        if not webhook_secret:
            logger.error(" FEDAPAY_WEBHOOK_SECRET non configuré")
            return False
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @db_transaction.atomic
    def _handle_approved_transaction(self, transaction_obj):
        """Active Premium ou Crée un Crédit (utilisé par le Webhook et CheckStatus)"""
        # Ne rien faire si déjà approuvé (protection contre les re-webhooks)
        if transaction_obj.status == 'approved':
            logger.warning(f" Transaction {transaction_obj.id} déjà approuvée. Ignoré.")
            return

        transaction_obj.status = 'approved'
        transaction_obj.approved_at = timezone.now()
        transaction_obj.save()
        
        user = transaction_obj.user
        
        # CAS 1: PREMIUM
        if transaction_obj.transaction_type == 'premium_subscription':
            subscription, created = PremiumSubscription.objects.get_or_create(user=user)
            subscription.transaction = transaction_obj
            subscription.activate_subscription(duration_days=30)
            
            user.is_premium_subscriber = True 
            user.save()
            
            logger.info(f" Premium activé: {user.email} jusqu'au {subscription.end_date.date()}")
        
        # CAS 2: TÉLÉCHARGEMENT UNIQUE
        elif transaction_obj.transaction_type == 'one_time_download':
            DownloadCredit.objects.get_or_create(
                user=user,
                cv=transaction_obj.cv,
                transaction=transaction_obj,
                defaults={'is_used': False}
            )
            
            user.download_credits = (user.download_credits or 0) + 1
            user.save()
            
            logger.info(f" Crédit ajouté: {user.email} - CV: {transaction_obj.cv.title if transaction_obj.cv else 'N/A'}")


# =====================================================================
# VUES DE PERMISSION ET CRÉDIT (Logique existante - INCHANGÉES)
# =====================================================================

class CheckDownloadPermissionView(APIView):
    """Vérifie si l'utilisateur peut télécharger le CV (Premium ou Crédit)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, cv_id):
        user = request.user
        
        try:
            cv = CV.objects.get(id=cv_id, owner=user)
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_premium_subscriber:
            try:
                subscription = PremiumSubscription.objects.get(user=user)
                if subscription.is_valid():
                    return Response({
                        'can_download': True,
                        'reason': 'premium',
                        'message': 'Téléchargement illimité (Premium)'
                    })
            except PremiumSubscription.DoesNotExist:
                pass
        
        unused_credit = DownloadCredit.objects.filter(
            user=user,
            cv=cv,
            is_used=False
        ).first()
        
        if unused_credit:
            return Response({
                'can_download': True,
                'reason': 'credit',
                'credit_id': unused_credit.id,
                'message': 'Crédit de téléchargement disponible'
            })
        
        return Response({
            'can_download': False,
            'reason': 'no_permission',
            'message': 'Abonnement Premium ou crédit requis'
        })


class ConsumeDownloadCreditView(APIView):
    """Consomme le crédit de téléchargement unique après le téléchargement réel."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        credit_id = request.data.get('credit_id')
        
        try:
            credit = DownloadCredit.objects.get(
                id=credit_id,
                user=request.user,
                is_used=False
            )
            
            if credit.use_credit(): 
                request.user.download_credits = max(0, request.user.download_credits - 1)
                request.user.save()
                
                logger.info(f" Crédit consommé: {credit_id} - User: {request.user.email}")
                return Response({'message': 'Crédit consommé avec succès'})
            else:
                return Response(
                    {'error': 'Crédit déjà utilisé'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except DownloadCredit.DoesNotExist:
            return Response(
                {'error': 'Crédit introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )