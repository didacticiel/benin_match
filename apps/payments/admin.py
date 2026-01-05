# apps/payments/admin.py

from django.contrib import admin
from .models import Transaction, PremiumSubscription, DownloadCredit

## Administration des Transactions

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_full_name',
        'transaction_type',
        'amount',
        'currency',
        'status',
        'created_at',
        'approved_at',
    )
    list_filter = (
        'status',
        'transaction_type',
        'currency',
        'created_at',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'fedapay_transaction_id',
        'description',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'cv',
                'description',
            )
        }),
        ('Détails de la Transaction', {
            'fields': (
                'transaction_type',
                'amount',
                'currency',
                'status',
            )
        }),
        ('Informations FedaPay', {
            'fields': (
                'fedapay_transaction_id',
                'fedapay_token',
                'metadata',
            ),
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
                'approved_at',
            )
        })
    )

    def get_full_name(self, obj):
        """Affiche le nom complet de l'utilisateur."""
        return obj.user.get_full_name() or obj.user.email
    get_full_name.short_description = 'Nom Complet'
    get_full_name.admin_order_field = 'user__first_name'


## Administration des Abonnements Premium

@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'is_active',
        'start_date',
        'end_date',
        'auto_renew',
        'is_valid_display',
    )
    list_filter = (
        'is_active',
        'auto_renew',
        'end_date',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    date_hierarchy = 'start_date'
    raw_id_fields = ('user', 'transaction',)
    
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'transaction',
            )
        }),
        ('Période d\'Abonnement', {
            'fields': (
                'start_date',
                'end_date',
                'is_active',
                'auto_renew',
            )
        }),
        ('Dates Système', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',), # Masque par défaut pour un affichage plus propre
        }),
    )
    
    def is_valid_display(self, obj):
        """Affiche l'état de validité actuel de l'abonnement."""
        if obj.is_valid():
            return '✅ Valide'
        return '❌ Expiré/Inactif'
    is_valid_display.short_description = 'Validité Actuelle'
    is_valid_display.boolean = True # Utilise une icône de coche/croix


## Administration des Crédits de Téléchargement

@admin.register(DownloadCredit)
class DownloadCreditAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'cv_title',
        'is_used',
        'created_at',
        'used_at',
    )
    list_filter = (
        'is_used',
        'created_at',
    )
    search_fields = (
        'user__email',
        'cv__title',
    )
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'cv', 'transaction',)
    
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'cv',
                'transaction',
            )
        }),
        ('Statut', {
            'fields': (
                'is_used',
                'used_at',
            )
        }),
        ('Date de Création', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def cv_title(self, obj):
        """Affiche le titre du CV associé."""
        return obj.cv.title if obj.cv else 'N/A'
    cv_title.short_description = 'Titre du CV'