from django.urls import path
from . import views

app_name = 'profiles'


urlpatterns = [
    path('profile/', views.ProfileListView.as_view(), name='list'), 
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'), # Le nouveau point d'entrée
    path('edit/', views.ProfileUpdateView.as_view(), name='edit'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='detail'),
    path('me/', views.DashboardView.as_view(), name='my_profile'), # Redirection vers le dashboard
]