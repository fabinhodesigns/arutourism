# arutourism/settings.py

import os
from pathlib import Path
import django_heroku

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurações Lidas do Ambiente ---
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = (os.environ.get('DEBUG') == 'True') # Será False no Heroku

# O django_heroku vai cuidar do ALLOWED_HOSTS
ALLOWED_HOSTS = []

# --- Aplicações Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages',
    'whitenoise.middleware.CompressedManifestStaticFilesStorage', # Para arquivos estáticos
    'django.contrib.staticfiles', 'widget_tweaks', 'core', 'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arutourism.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
WSGI_APPLICATION = 'arutourism.wsgi.application'

# O DATABASES pode ser um dicionário vazio. O django-heroku vai preenchê-lo.
DATABASES = {}

# ... (seu AUTH_PASSWORD_VALIDATORS e Internationalization) ...

# --- Configurações de Arquivos ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}
LOGIN_URL = '/login/'

# --- ATIVAÇÃO FINAL DO DJANGO-HEROKU ---
# Deixe esta linha no final. Ela configura TUDO: banco de dados, hosts, estáticos, etc.
django_heroku.settings(locals())