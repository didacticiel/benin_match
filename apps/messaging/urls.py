from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='list'),
    path('thread/<int:pk>/', views.ChatView.as_view(), name='detail'),
    # Route Polling (Simule le temps réel)
    path('thread/<int:pk>/new/', views.NewMessagesView.as_view(), name='poll'),
]