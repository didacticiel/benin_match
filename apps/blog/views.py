from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Count, F, Q
from .models import Post, Category

# =========================================================================
# 1. LISTE DES ARTICLES (Page d'accueil du Blog)
# =========================================================================
class PostListView(ListView):
    """
    Affiche la grille des articles.
    Optimisé avec select_related pour charger l'auteur en 1 requête.
    """
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 6  # 6 articles par page

    def get_queryset(self):
        # Filtrer uniquement les articles publiés
        # order_by explicit pour être sûr de l'ordre chronologique inversé
        return Post.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('categories').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculer les catégories avec le nombre d'articles pour la Sidebar
        # On cache le résultat (`prefetch_related` n'est pas applicable ici car on veut un count)
        context['categories'] = Category.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0).order_by('name')
        
        return context


# =========================================================================
# 2. DÉTAIL D'UN ARTICLE (Page de lecture)
# =========================================================================
class PostDetailView(DetailView):
    """
    Affiche un article, incrémente les vues et récupère les articles similaires.
    """
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        # Surcharge pour gérer l'incrémentation des vues au chargement de la page
        obj = super().get_object(queryset=queryset)
        
        # Incrémentation du compteur de vues (Simple mais efficace pour un petit blog)
        # Utilisation de F() expressions pour éviter la course conditionnelle en base de données
        Post.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        return obj

    def get_queryset(self):
        # Optimisation : Charger l'auteur immédiatement
        return super().get_queryset().select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Articles Similaires (Related Posts)
        # On récupère les ID des catégories de l'article actuel pour la requête
        # C'est beaucoup plus performant que de faire une jointure N+1
        category_ids = self.object.categories.values_list('id', flat=True)
        
        context['related_posts'] = Post.objects.filter(
            status='published',
            categories__id__in=category_ids
        ).exclude(id=self.object.id).select_related('author').distinct()[:3]

        # 2. Toutes les catégories (Pour le breadcrumb/tags en haut de l'article)
        context['categories'] = Category.objects.all()

        return context


# =========================================================================
# 3. LISTE PAR CATÉGORIE (Filtrage via URL)
# =========================================================================
class CategoryPostListView(ListView):
    """
    Affiche les articles d'une catégorie spécifique (ex: /blog/amour/)
    """
    model = Post
    template_name = "blog/post_list.html"  # On réutilise le même template que la liste principale
    context_object_name = "posts"
    paginate_by = 6

    def get_queryset(self):
        # Récupérer la catégorie via le slug dans l'URL
        # On le stocke dans self pour l'utiliser dans get_context_data
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        
        # Filtrer les articles appartenant à cette catégorie
        return Post.objects.filter(
            status='published',
            categories=self.category
        ).select_related('author').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # On passe la catégorie courante pour le template (ex: "Titre de la catégorie" dans le header)
        context['current_category'] = self.category
        return context