from django.urls import path
from django.views.generic import TemplateView # Pour la page de succès
from . import views

app_name = 'contact'

urlpatterns = [
    # Page principale du formulaire
    path('', views.ContactView.as_view(), name='contact'),
    
    # Page de succès (Merci) - Utilise TemplateView pour afficher juste un HTML
    path('success/', TemplateView.as_view(template_name='contact/success.html'), name='success'),
]