import sys
import os
from pathlib import Path
from datetime import timedelta
import environ

# =========================================================================
# 0. INITIALISATION ENVIRON
# =========================================================================
env = environ.Env()
# Remonte de config/settings/ -> config/ -> benin_match/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Lecture du fichier .env à la racine du projet
environ.Env.read_env(str(BASE_DIR / '.env'))

# =========================================================================
# 1. CONFIGURATION CORE
# =========================================================================
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-en-prod')
DEBUG = env.bool('DEBUG', default=False)

# Ajoute ton domaine PythonAnywhere ici en production (ex: tonsite.pythonanywhere.com)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

SITE_ID = 1
ROOT_URLCONF = 'config.urls'      # <--- CORRIGÉ (était src.urls)
WSGI_APPLICATION = 'config.wsgi.application' # <--- CORRIGÉ (était src.wsgi.application)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================================
# 2. APPLICATIONS
# =========================================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', 
    'django.contrib.sitemaps',
    'django.contrib.humanize', # Utile pour "Il y a 2 minutes"
]

THIRD_PARTY_APPS = [
    # REST API (Pour future App Mobile ou API interne)
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'easy_thumbnails',
    'ckeditor',          # Pour le Blog (éditeur riche)
    'ckeditor_uploader',
    'django_htmx',       # Support HTMX
    'crispy_forms',      # Formulaires propres
    'crispy_tailwind',   # Intégration Tailwind
    'tailwind',          # Intégration Tailwind CSS
    # Authentification Sociale & Email
    'allauth',
    'allauth.account', 
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook', # Ajouté pour la diaspora
]

LOCAL_APPS = [
    'apps.core',         # Utilitaires globaux
    'apps.users',        # Auth User custom
    'apps.profiles',     # Profils détaillés, photos
    'apps.search',       # Moteur de recherche & Algo matching
    'apps.messaging',    # Chat interne
    'apps.blog',         # Blog pour le SEO
    'apps.contact'
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =========================================================================
# 3. MIDDLEWARE
# =========================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- IMPORTANT POUR PYTHONANYWHERE
    'django_htmx.middleware.HtmxMiddleware', 
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

# =========================================================================
# 4. TEMPLATES
# =========================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Dossier templates à la racine
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.messaging.context_processors.unread_messages_count',
            ],
        },
    },
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

"""
# =========================================================================
# 5. BASE DE DONNÉES (Postgres sur PA, SQLite en local)
# =========================================================================
import dj_database_url

# Par défaut SQLite en local, on lit DATABASE_URL en prod
DATABASE_URL = env('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
    )
}

# Forcer SSL si on n'est pas en SQLite (Utile pour PA)
if 'sqlite' not in DATABASES['default']['ENGINE']:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
"""

# =========================================================================
# 5. BASE DE DONNÉES (Postgres partout !)
# =========================================================================
import dj_database_url

# On lit l'URL depuis le fichier .env. Pas de fallback SQLite.
# Si cette variable n'est pas définie, Django plantera (ce qui est normal).
DATABASE_URL = env('DATABASE_URL')

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL, 
        conn_max_age=600,      # Persister la connexion (Performance)
        ssl_require=not DEBUG, # Active SSL automatiquement si DEBUG=False
    )
}

# Sécurité additionnelle : on s'assure que SSL est bien 'require' en prod
if not DEBUG:
    # Vérifie si l'URL ne contient pas déjà sslmode=disable
    if 'sslmode=disable' not in DATABASES.get('default', {}).get('NAME', ''):
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default']['OPTIONS']['sslmode'] = 'require'
        
# IMPORTANT: On référence le User model dans apps.users
AUTH_USER_MODEL = 'users.User'


# =========================================================================
# 6. AUTHENTIFICATION & ALLAUTH
# =========================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuration Allauth pour un dating app
# On peut vouloir forcer la vérification email plus tard
ACCOUNT_EMAIL_VERIFICATION = 'none' # 'none' pour le dev, 'mandatory' pour la prod
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Login par email
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_AUTO_SIGNUP = True
# Redirection après login/inscription (vers la page de recherche ou d'accueil)
LOGIN_REDIRECT_URL = 'profiles:home'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# =========================================================================
# 7. DRF & JWT (Optionnel mais utile pour une API mobile future)
# =========================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

JWT_COOKIE_SECURE = env.bool('JWT_COOKIE_SECURE', default=not DEBUG) 
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = "Lax"

# =========================================================================
# 8. STATICS, MEDIA & EMAIL
# =========================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # Où collectstatic va mettre les fichiers
STATICFILES_DIRS = [BASE_DIR / 'static'] # Dossier source

# WhiteNoise pour gérer les fichiers statiques en prod
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Email (Nécessaire pour la vérification compte sur PythonAnywhere)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='contact@beninmatch.bj')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# =========================================================================
# 9. CKEDITOR (Pour le Blog)
# =========================================================================
CKEDITOR_UPLOAD_PATH = "uploads/ckeditor/"
CKEDITOR_CONFIGS = {
    'default': {
        'skin': 'moono-lisa',
        'toolbar': 'Custom',
        'extraPlugins': 'codesnippet',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Blockquote'],
            ['Link', 'Unlink', 'Image'],
            ['Styles', 'Format', 'FontSize'],
            ['Maximize', 'Source'],
        ],
    }
}
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

# =========================================================================
# 10. SOCIAL AUTH (GOOGLE & FACEBOOK)
# =========================================================================
GOOGLE_OAUTH_CLIENT_ID = env('GOOGLE_OAUTH_CLIENT_ID', default='')
GOOGLE_OAUTH_CLIENT_SECRET = env('GOOGLE_OAUTH_CLIENT_SECRET', default='')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    },
    'facebook': {
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'rerequest'}
    }
}

# =========================================================================
# 11. I18N (Internationalisation)
# =========================================================================
LANGUAGE_CODE = 'fr-fr'
# Fuseau horaire du Bénin
TIME_ZONE = env('TIME_ZONE', default="Africa/Porto-Novo") 

USE_I18N = True
USE_TZ = True
LANGUAGES = [('fr', 'Français'), ('en', 'English')]
LOCALE_PATHS = [BASE_DIR / 'locale']