# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Change 'signup' par 'register' pour correspondre au {% url 'users:register' %} de ta navbar
    path('signup/', views.register_view, name='register'), 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]