from django.contrib import admin
from .models import Message, Thread

# --- 1. INLINE POUR LES MESSAGES (Affichage dans le Thread) ---
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0  # Pas de ligne vide par défaut
    readonly_fields = ('sender', 'content', 'created_at', 'image')
    can_delete = False
    fields = ('sender', 'content', 'created_at', 'image', 'is_read')


# --- 2. PAGE PRINCIPALE DES CONVERSATIONS ---
@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    
    # OPTIMISATION CRITIQUE :
    # On charge les participants en même temps que les threads (1 seule requête)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants')

    # MÉTHODE PERSONNALISÉE pour afficher les participants
    # (Remplace le champ 'participants' pour éviter l'erreur SystemCheck)
    def get_participants_list(self, obj):
        """Affiche la liste des emails des participants, séparés par une virgule"""
        return ", ".join([u.email for u in obj.participants.all()])

    # Liste des colonnes (On utilise la méthode custom, pas le champ M2M)
    list_display = ('get_participants_list', 'updated_at', 'is_active')
    
    # Filtres latéraux
    list_filter = ('is_active', 'updated_at')
    
    # Barre de recherche (On peut toujours chercher dans le champ participants)
    search_fields = ('participants__email',)
    
    # Inline des messages
    inlines = [MessageInline]


# --- 3. PAGE DES MESSAGES ---
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'content', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content',)
    
    # Actions en masse
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        """Marquer tous les messages sélectionnés comme lus"""
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lu"