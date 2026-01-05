#settings/local.py

from .base import *

# =========================================================================
# 1. DEBUG & SÉCURITÉ LOCALE
# =========================================================================
DEBUG = True

# Autorise le serveur local et les tests
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '.testserver']

# Désactiver les cookies sécurisés (SSL) pour le développement local
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =========================================================================
# 2. EMAIL (Développement)
# =========================================================================
# En local, on imprime les emails dans la console plutôt que de les envoyer
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =========================================================================
# 3. BASE DE DONNÉES
# =========================================================================
# Note: Comme tu as configuré DATABASE_URL dans ton fichier .env,
# il n'est pas nécessaire de redéfinir DATABASES ici.
# Django va automatiquement utiliser l'URL du fichier .env.
# Si tu veux une base locale différente du .env, tu peux le faire ici.

# Exemple (si tu voulais forcer SQLite malgré tout, décommente ci-dessous):
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }