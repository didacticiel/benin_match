# apps/core/urls.py

from django.urls import path
from .views import HomePageView, AboutPageView, ContactPageView, ServicePageView

app_name = 'core'

urlpatterns = [
    # Page d'accueil (URL: /)
    path('', HomePageView.as_view(), name='home'), 
    
    # Page À propos (URL: /about/)
    path('about/', AboutPageView.as_view(), name='about'), 
    
    # Page Contact (URL: /contact/)
    path('contact/', ContactPageView.as_view(), name='contact'),
    
    # Page Services (URL: /services/)
    path('services/', ServicePageView.as_view(), name='service'),
]