from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField
# ====================================================================
# 1. Catégories
# ====================================================================

class Category(models.Model):
    """Représente une catégorie pour les articles de blog."""
    
    #  Champ principal (Nom affiché)
    name = models.CharField(max_length=255, unique=True, verbose_name="Nom de la catégorie")
    
    #  Champ SEO (URL propre)
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug (URL)")
    
    # ⚙️ Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ('name',)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Génération automatique du slug si non fourni
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# ====================================================================
# 2. Articles (Posts)
# ====================================================================

class Post(models.Model):
    """Représente un article de blog complet."""

    #  Relations
    # L'auteur est un utilisateur de notre système
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # On garde l'article même si l'auteur est supprimé
        null=True, 
        related_name='blog_posts', 
        verbose_name="Auteur",
        blank=True,
    )
    # Relation Many-to-Many avec les catégories
    categories = models.ManyToManyField(
        Category, 
        related_name='posts', 
        verbose_name="Catégories"
    )

    #  Contenu de Base
    title = models.CharField(max_length=255, unique=True, verbose_name="Titre de l'article")
    
    #  Champ SEO (URL propre)
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug (URL)")
    
    #  Image de Couverture
    cover_image = models.ImageField(
        upload_to='blog/covers/%Y/%m/%d/', 
        blank=True, 
        null=True, 
        verbose_name="Image de couverture"
    )
    
    #  Contenu (Utilise TextField pour le contenu riche. Un éditeur comme TinyMCE ou un champ Markdown sera nécessaire plus tard.)
    content = RichTextUploadingField(verbose_name="Contenu de l'article")
    
    #  SEO (Pour les moteurs de recherche)
    seo_description = models.CharField(
        max_length=160, 
        blank=True, 
        verbose_name="Méta-description (SEO)"
    )
    
    # Statut et Publication
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name="Statut"
    )
    
    #  Dates et Métriques
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de publication")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #  Métriques (pour affichage pro : ex. "5 min de lecture")
    reading_time = models.PositiveSmallIntegerField(default=0, verbose_name="Temps de lecture (min)")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        # Tri par défaut: le plus récent publié en premier
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Génération automatique du slug si non fourni
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Si l'article est marqué comme publié sans date, on met la date actuelle
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retourne l'URL canonique de l'article pour le frontend."""
        # Note: Nous devrons définir ce nom d'URL dans apps/blog/urls.py
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
# apps/blog/models.py (Continuation, à ajouter après la classe Post)

# ====================================================================
# 3. Commentaires (Comments)
# ====================================================================

class Comment(models.Model):
    """Représente un commentaire sur un article de blog."""

    #  Relations
    # Lien vers l'article commenté
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,  # Supprimer les commentaires si l'article est supprimé
        related_name='comments',
        verbose_name="Article"
    )
    # L'utilisateur qui a posté le commentaire
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Garder le commentaire même si l'utilisateur est supprimé
        null=True,
        related_name='blog_comments',
        verbose_name="Auteur du commentaire"
    )
    
    #  Contenu
    content = models.TextField(verbose_name="Contenu du commentaire")
    
    #  Statut et Modération
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé pour publication")
    
    #  Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        # Tri par défaut : les plus récents en premier
        ordering = ('-created_at',)

    def __str__(self):
        # Affichage : "Commentaire par [Auteur] sur [Titre de l'article]"
        return f"Commentaire par {self.author.username if self.author else 'Utilisateur supprimé'} sur {self.post.title[:30]}..."


# ====================================================================
# 4. Notes et Évaluations (PostRating)
# ====================================================================

class PostRating(models.Model):
    """Permet aux utilisateurs de donner une note à un article (ex: sur 5 étoiles)."""

    # Relations
    # Lien vers l'article noté
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name="Article"
    )
    # L'utilisateur qui a donné la note
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_ratings',
        verbose_name="Utilisateur"
    )
    
    #  Valeur de la note (entre 1 et 5)
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    score = models.IntegerField(choices=RATING_CHOICES, verbose_name="Note (1 à 5)")

    #  Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Note d'article"
        verbose_name_plural = "Notes d'articles"
        #  IMPORTANT : Assure qu'un utilisateur ne peut noter un article qu'une seule fois
        unique_together = ('post', 'user') 
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.username} a noté {self.post.title[:30]}... avec {self.score}/5"