# config/settings/testing.py
from .local import *  # Hérite de local (Postgres, Debug True, etc.)

# On surcharge uniquement pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:', # Base de données en mémoire ultra-rapide pour les tests
    }
}

# Désactiver certaines choses lourdes pour les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher', # Plus rapide que bcrypt pour les tests
]