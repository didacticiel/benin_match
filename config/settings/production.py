#settings/production.py

from .base import *

# =========================================================================
# 1. DEBUG & HOSTS
# =========================================================================
DEBUG = False

# PythonAnywhere fournit souvent des variables d'environnement, mais on peut aussi lister le domaine ici.
# Le .pythonanywhere.com gère les sous-domaines (www, etc.)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.pythonanywhere.com'])

# =========================================================================
# 2. SÉCURITÉ (HSTS & HTTPS)
# =========================================================================
SECURE_SSL_REDIRECT = True          # Force HTTPS
SESSION_COOKIE_SECURE = True         # Cookies uniquement sur HTTPS
CSRF_COOKIE_SECURE = True            # CSRF uniquement sur HTTPS
SECURE_BROWSER_XSS_FILTER = True     # Filtre XSS navigateur
SECURE_CONTENT_TYPE_NOSNIFF = True   # Protection sniffing type MIME
X_FRAME_OPTIONS = 'DENY'             # Protection clickjacking
SECURE_HSTS_SECONDS = 31536000       # HSTS pendant 1 an (Obligatoire pour HTTPS strict)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Désactiver la possibilité de montrer les templates en cas d'erreur (pour cacher le code)
TEMPLATES[0]['OPTIONS']['debug'] = False

# =========================================================================
# 3. EMAIL (Configuration SMTP)
# =========================================================================
# En production, on utilise un vrai serveur SMTP.
# PythonAnywhere en propose un, sinon tu peux utiliser Brevo (SendinBlue) ou Amazon SES.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='contact@beninmatch.bj')

# =========================================================================
# 4. STATIC & MEDIA FILES (Chemins absolus)
# =========================================================================
# Assure-toi que ces dossiers existent et ont les droits d'écriture si besoin
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Forcer l'utilisation de WhiteNoise pour servir les fichiers statiques compressés
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =========================================================================
# 5. LOGGING (Indispensable sur PythonAnywhere)
# =========================================================================
# PythonAnywhere capture stderr et stdout dans les logs du web.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # Optionnel : Sauvegarder dans un fichier
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'filename': BASE_DIR / 'logs/django.log',
        #     'formatter': 'verbose',
        # },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}