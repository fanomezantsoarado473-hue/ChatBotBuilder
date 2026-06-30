import os
from pathlib import Path
import dj_database_url  # Ilaina raha hampiasa PostgreSQL any amin'ny Render (Azo install-ena: pip install dj-database-url)

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep this secret in production!
# Maka avy amin'ny Render config, raha tsy misy dia mampiasa ilay default
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-key-in-production')

# =========================
# PRODUCTION SETTINGS
# =========================
# Mivadika True raha ao amin'ny solosainao (tsy misy RENDER amin'ny env), mivadika False any amin'ny Render
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = [
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

# =========================
# APPLICATIONS
# =========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party
    'rest_framework',
    'corsheaders',

    # your app
    'api',
]

# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ⚡ Ilaina mampiseho static files any amin'ny Render (pip install whitenoise)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot_backend.wsgi.application'

# =========================
# DATABASE (SMART DEV / PROD SWITCH)
# =========================
if 'RENDER' in os.environ:
    # Any amin'ny Render: Raha nampiditra DATABASE_URL ianao dia iny no miasa, raha tsy izany dia SQLite vonjimaika
    DATABASES = {
    'default': dj_database_url.config(
        # Raha ao an-trano (local), dia ity PostgreSQL-nao ity no miasa:
        default='postgresql://postgres:rado1234@localhost:5432/boltchat',
        conn_max_age=600
    )
}
else:
    # Ao amin'ny solosainao (Local Dev): Ny PostgreSQL-nao mahazatra no miasa
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'boltchat',
            'USER': 'postgres',
            'PASSWORD': 'rado1234',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

# =========================
# INTERNATIONALIZATION
# =========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Indian/Antananarivo'
USE_I18N = True
USE_TZ = True

# =========================
# STATIC FILES (IMPORTANT FOR DEPLOYMENT)
# =========================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Fanamorana ny static files ho an'ny Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =========================
# DEFAULT AUTO FIELD
# =========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# CORS (React Native / Expo)
# =========================
CORS_ALLOW_ALL_ORIGINS = True