# src/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    # ----------------------------------------------------
    # 1. ADMIN DJANGO
    # ----------------------------------------------------
    path('admin/', admin.site.urls),

    # ----------------------------------------------------
    # 2. ENDPOINTS API (Version 1)
    # ----------------------------------------------------
    
    # 2.1. USERS API (Authentification JWT, Google Auth)
    path('api/v1/users/', include('apps.users.urls_api', namespace='users_api')),
    
    # 2.2. BLOG API (Articles et Catégories)
    path('api/v1/blog/', include('apps.blog.urls_api', namespace='blog_api')),

    # 2.3. PORTFOLIO API - À faire
    # path('api/v1/portfolio/', include('apps.portfolio.urls_api', namespace='portfolio_api')),
    
    # ----------------------------------------------------
    # 3. VUES DJANGO / HTMX (FRONTEND PUBLIC)
    # ----------------------------------------------------
    
    # 3.1. CORE (Page d'accueil, À propos)
    path('', include('apps.core.urls')), 
    
    # 3.2. CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # 3.3. USERS (Templates : signup, login, logout)
    # ⚠️ CORRECTION : Namespace différent pour éviter les conflits
    path('users/', include('apps.users.urls', namespace='users_views')),
    
    # 3.4. BLOG (Affichage public des articles)
    path('blog/', include('apps.blog.urls', namespace='blog')),
    
    # 3.5. PORTFOLIO - À faire
    path('portfolio/', include('apps.portfolio.urls', namespace='portfolio')),
]

# ----------------------------------------------------
# 4. FICHIERS STATIQUES, MÉDIAS ET DEBUG TOOLBAR
# ----------------------------------------------------

if settings.DEBUG:
    # 4.1. Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    # 4.2. Fichiers Médias et Statiques
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)