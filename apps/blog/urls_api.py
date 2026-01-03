# apps/blog/urls_api.py

from django.urls import path

app_name = 'blog_api'

# Le contenu du routeur DRF que nous avions préparé
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
# router.register(...)

urlpatterns = router.urls

# Si vous n'aviez pas installé djangorestframework, remplacez-le par:
# urlpatterns = []