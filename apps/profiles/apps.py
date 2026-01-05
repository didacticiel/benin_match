
from django.apps import AppConfig

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.profiles'
    verbose_name = 'Profils'

    def ready(self):
        # Importer le signal à l'initialisation de l'app
        from . import signals  
