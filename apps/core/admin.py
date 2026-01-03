from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste
    list_display = ('name', 'subject', 'email', 'created_at', 'is_read_status')
    
    # Filtres sur le côté droit
    list_filter = ('is_read', 'created_at')
    
    # Champs de recherche
    search_fields = ('name', 'email', 'subject', 'message')
    
    # Date hiérarchique pour naviguer par année/mois
    date_hierarchy = 'created_at'
    
    # Nombre d'éléments par page
    list_per_page = 20
    
    # Actions personnalisées pour marquer comme lu/non lu
    actions = ['mark_as_read', 'mark_as_unread']

    def is_read_status(self, obj):
        """Affiche une icône visuelle pour le statut de lecture"""
        if obj.is_read:
            return True
        return False
    is_read_status.boolean = True
    is_read_status.short_description = "Lu"

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lus"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Marquer comme non lus"

    # Rendre les champs du message en lecture seule pour éviter les modifs accidentelles
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')

    # Organisation des champs dans le détail du message
    fieldsets = (
        ('Informations Expéditeur', {
            'fields': ('name', 'email')
        }),
        ('Contenu du Message', {
            'fields': ('subject', 'message')
        }),
        ('Statut & Dates', {
            'fields': ('is_read', 'created_at')
        }),
    )