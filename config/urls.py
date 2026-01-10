from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    # 1. ADMIN
    path('admin/', admin.site.urls),

    # 2. CORE (Home, About, Contact)
    path('', include('apps.core.urls', namespace='core')),
    
    # 3. USERS (Inscription, Login)
    path('users/', include('apps.users.urls', namespace='users')),
    
    # 4. PROFILES (Liste, Détail, Édition) <--- C'EST CE QUI MANQUAIT
    path('profiles/', include('apps.profiles.urls', namespace='profiles')),
    
    # 5. BLOG
    path('blog/', include('apps.blog.urls', namespace='blog')),
    
    # 6. MESSAGING (Messages) - Pour les liens dans la navbar
    path('messages/', include('apps.messaging.urls', namespace='messaging')),
    
    # 7. SEARCH (Recherche)
    path('search/', include('apps.search.urls', namespace='search')),
    
    # 8 . CONTACT (Contact)
    path('contact/', include('apps.contact.urls', namespace='contact')),
    
    # 9. CKEDITOR
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# 10. STATIC & MEDIA
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)