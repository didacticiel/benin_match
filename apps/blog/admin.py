from django.contrib import admin
from django import forms
from .models import Category, Post, Comment, PostRating # <-- Mise à jour des imports
from ckeditor_uploader.widgets import CKEditorUploadingWidget

# =============================================================
# 1. Personnalisation du Modèle Category
# =============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Category."""
    
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('created_at',)


# =============================================================
# 2. Inlines pour l'Édition du Post (Commentaires et Notes)
# =============================================================

class CommentInline(admin.TabularInline):
    """Affiche les commentaires directement dans la page d'édition de l'article."""
    model = Comment
    extra = 0 # Ne pas afficher de lignes vides par défaut
    fields = ('author', 'content', 'is_approved', 'created_at')
    readonly_fields = ('author', 'content', 'created_at') # Empêcher l'édition du contenu/auteur dans l'inline
    list_display_links = ('content',) # Pour rendre le contenu cliquable
    
class RatingInline(admin.TabularInline):
    """Affiche les notes données à l'article directement dans la page d'édition."""
    model = PostRating
    extra = 0
    fields = ('user', 'score', 'created_at')
    readonly_fields = ('user', 'score', 'created_at')


# =============================================================
# 3. Personnalisation du Modèle Post
# =============================================================

# Utiliser le widget CKEditor pour le champ 'content'
class PostAdminForm(forms.ModelForm):
    """Formulaire personnalisé pour utiliser CKEditor pour le champ content."""
    
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Post
        fields = '__all__'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Post."""
    
    form = PostAdminForm
    
    #  AJOUT : Inlines pour afficher Commentaires et Notes sur la page du Post
    inlines = [CommentInline, RatingInline] 
    
    # Affichage dans la liste
    list_display = (
        'title', 
        'author', 
        'status', 
        'get_category_list', # Nouvelle méthode pour afficher les catégories
        'published_at', 
        'reading_time',
        'views_count',
    )
    list_display_links = ('title',) # Rendre le titre cliquable

    # Filtres et Recherche
    list_filter = ('status', 'categories', 'published_at', 'created_at')
    search_fields = ('title', 'content', 'seo_description')
    
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',) 
    actions = ['make_published', 'make_draft']
    
    # Organisation du formulaire d'édition
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'status', 'author', 'categories', 'cover_image')
        }),
        ('Contenu de l\'article', {
            'fields': ('content',),
        }),
        ('Publication et SEO', {
            'fields': ('published_at', 'seo_description'),
            'classes': ('collapse',),
        }),
        ('Statistiques (Lecture seule)', {
            'fields': ('reading_time', 'views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'reading_time', 'views_count')

    # --- Méthode d'aide pour l'affichage des catégories dans list_display ---
    @admin.display(description='Catégories')
    def get_category_list(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
        
   

    @admin.action(description='Marquer les articles sélectionnés comme PUBLIÉS')
    def make_published(self, request, queryset):
        for post in queryset:
            post.status = 'published'
            post.save() 
        self.message_user(request, f"{queryset.count()} articles ont été marqués comme publiés.", level='success')

    @admin.action(description='Marquer les articles sélectionnés comme BROUILLONS')
    def make_draft(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f"{queryset.count()} articles ont été marqués comme brouillons.", level='warning')


# =============================================================
# 4. Enregistrement des modèles Commentaires et Notes
# =============================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Gestion des commentaires (utilisé surtout pour la modération)."""
    list_display = ('post', 'author', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'post__title', 'author__username')
    actions = ['approve_comments', 'disapprove_comments']
    
    # Rendre les champs post et author en lecture seule pour éviter les changements
    readonly_fields = ('post', 'author', 'created_at')
    
    @admin.action(description='Approuver les commentaires sélectionnés')
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} commentaires approuvés.")

    @admin.action(description='Désapprouver les commentaires sélectionnés')
    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} commentaires désapprouvés.")


@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):
    """Gestion des notes des articles."""
    list_display = ('post', 'user', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('post__title', 'user__username')
    readonly_fields = ('post', 'user', 'score', 'created_at')