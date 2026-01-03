import sys
import os
from pathlib import Path
from datetime import timedelta
import environ

# =========================================================================
# 0. INITIALISATION ENVIRON
# =========================================================================
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Lecture du fichier .env
environ.Env.read_env(str(BASE_DIR / '.env'))

# =========================================================================
# 1. CONFIGURATION CORE
# =========================================================================
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dummy-key-for-ci')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

SITE_ID = 1
ROOT_URLCONF = 'src.urls'
WSGI_APPLICATION = 'src.wsgi.application'
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
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'easy_thumbnails',
    'django_redis',
    'ckeditor', 
    'ckeditor_uploader',
    'django_htmx', 
    'allauth',
    'allauth.account', 
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.blog',
    'apps.portfolio',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =========================================================================
# 3. MIDDLEWARE
# =========================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# =========================================================================
# 5. BASE DE DONNÉES (Protection SQLite)
# =========================================================================
import dj_database_url

DATABASE_URL = env('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
    )
}

# On n'ajoute SSL QUE si on utilise un moteur autre que SQLite
if 'sqlite' not in DATABASES['default']['ENGINE']:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
    
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

# Paramètres modernes (plus de warnings)
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email', 'password1', 'password2']
# =========================================================================
# 7. DRF & JWT
# =========================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
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

# Cookies JWT
JWT_COOKIE_SECURE = env.bool('JWT_COOKIE_SECURE', default=not DEBUG) 
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = "Lax"

# =========================================================================
# 8. STATICS, MEDIA & EMAIL
# =========================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@abdouldidacticiel.bj')

# =========================================================================
# 9. CKEDITOR
# =========================================================================
CKEDITOR_UPLOAD_PATH = "uploads/ckeditor/"
CKEDITOR_CONFIGS = {
    'default': {
        'skin': 'moono-lisa',
        'toolbar': 'Custom',
        'extraPlugins': 'codesnippet',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Blockquote', 'JustifyLeft', 'JustifyCenter', 'JustifyRight'],
            ['Link', 'Unlink', 'Image', 'Table', 'HorizontalRule'],
            ['Styles', 'Format', 'Font', 'FontSize', 'TextColor'],
            ['Maximize', 'Source'],
        ],
    }
}
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]
# =========================================================================
# 10. SOCIAL AUTH (GOOGLE)
# =========================================================================
GOOGLE_OAUTH_CLIENT_ID = env('GOOGLE_OAUTH_CLIENT_ID', default='')
GOOGLE_OAUTH_CLIENT_SECRET = env('GOOGLE_OAUTH_CLIENT_SECRET', default='')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

# =========================================================================
# 11. I18N
# =========================================================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = env('TIME_ZONE', default="Africa/Porto-Novo")
USE_I18N = True
USE_TZ = True
LANGUAGES = [('fr', 'Français'), ('en', 'English')]
LOCALE_PATHS = [BASE_DIR / 'locale']