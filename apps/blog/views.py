#apps/blog/views.py
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Count
from .models import Post, Category

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        # On ne récupère que les articles publiés
        return Post.objects.filter(status='published').select_related('author').prefetch_related('categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Liste des catégories avec le nombre d'articles pour la sidebar
        context['categories'] = Category.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0)
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        # On incrémente le compteur de vues à chaque lecture
        obj = super().get_object(queryset=queryset)
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Articles similaires basés sur la catégorie
        context['related_posts'] = Post.objects.filter(
            status='published',
            categories__in=self.object.categories.all()
        ).exclude(id=self.object.id).distinct()[:3]
        return context

class CategoryPostListView(ListView):
    """Affiche les articles d'une catégorie spécifique."""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.objects.filter(status='published', categories=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = self.category
        return context