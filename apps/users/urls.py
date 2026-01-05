from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('inscription/', views.register_view, name='register'), 
    path('connexion/', views.CustomLoginView.as_view(), name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('google-auth/', views.google_auth_view, name='google_auth'),
]