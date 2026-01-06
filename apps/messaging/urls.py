# apps/messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='list'),
    path('thread/<int:pk>/', views.ChatView.as_view(), name='detail'),
    path('thread/<int:pk>/poll/', views.NewMessagesView.as_view(), name='poll'),
    path('thread/<int:pk>/check/', views.CheckNewMessagesView.as_view(), name='check'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
]