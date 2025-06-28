import os
from pathlib import Path
import django_heroku
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Use os.environ.get para pegar as variáveis, com um valor padrão para segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-padrao-para-evitar-crash')
DEBUG = os.environ.get('DEBUG') == 'True'

ALLOWED_HOSTS = [] # O django_heroku vai cuidar disso

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages',
    'whitenoise.middleware.CompressedManifestStaticFilesStorage',
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

# Configuração de banco de dados simples que o Heroku entende
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# ... AUTH_PASSWORD_VALIDATORS e Internationalization ...

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}
LOGIN_URL = '/login/'

# Ativação do Django-Heroku no final
django_heroku.settings(locals())