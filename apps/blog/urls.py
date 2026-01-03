from django.urls import path
from . views import PostListView, PostDetailView, CategoryPostListView
app_name = 'blog'

urlpatterns = [
    # Liste de tous les articles
    path('', PostListView.as_view(), name='post_list'),
    
    # Détail d'un article
    path('article/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
    
    # Articles par catégorie
    path('categorie/<slug:slug>/', CategoryPostListView.as_view(), name='category_posts'),
]