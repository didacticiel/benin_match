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
    # 2. FRONTEND DJANGO / HTMX (PAGES HTML)
    # ----------------------------------------------------
    
    # 2.1. CORE (Page d'accueil, À propos, Contact)
    path('', include('apps.core.urls', namespace='core')),
    
    # 2.2. USERS (Inscription, Connexion, Déconnexion)
    # On utilise 'users' comme namespace pour correspondre aux templates
    path('users/', include('apps.users.urls', namespace='users')),
    
    # 2.3. BLOG (Affichage public des articles)
    path('blog/', include('apps.blog.urls', namespace='blog')),
    
    # 2.4. CKEDITOR (Éditeur pour l'admin/blog)
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # ----------------------------------------------------
    # 3. APPS FUTURES (Commentées pour ne pas planter)
    # ----------------------------------------------------
    # path('profiles/', include('apps.profiles.urls', namespace='profiles')),
    # path('search/', include('apps.search.urls', namespace='search')),
    # path('messaging/', include('apps.messaging.urls', namespace='messaging')),
]

# ----------------------------------------------------
# 4. FICHIERS STATIQUES, MÉDIAS ET DEBUG TOOLBAR
# ----------------------------------------------------

if settings.DEBUG:
    # 4.1. Debug Toolbar (Optionnel, assure-toi d'avoir 'debug_toolbar' dans INSTALLED_APPS)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    # 4.2. Fichiers Médias (Images uploadées)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 4.3. Fichiers Statiques (CSS/JS) - Servis localement
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)