from pathlib import Path
from urllib.parse import urlparse
import os, sys
import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# .env
env = environ.Env(
    DEBUG=(bool, False),
    ENVIRONMENT=(str, "development"),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Flags básicas
DEBUG = env.bool("DEBUG", default=False)
ENVIRONMENT = env.str("ENVIRONMENT", default=("production" if not DEBUG else "development"))
IS_PROD = (ENVIRONMENT == "production") or (not DEBUG)

SECRET_KEY = env("SECRET_KEY", default=None)
if not SECRET_KEY:
    # Em dev, se quiser, gera uma fallback fraca; em prod deve estar setada
    # Melhor falhar cedo em prod:
    if not DEBUG:
        raise RuntimeError("SECRET_KEY não definido. Configure no ambiente.")
    SECRET_KEY = "dev-insecure-key"

# Detecta host do Render (se existir)
RENDER_EXTERNAL_URL = env("RENDER_EXTERNAL_URL", default=None)
parsed_render = urlparse(RENDER_EXTERNAL_URL) if RENDER_EXTERNAL_URL else None
render_host = parsed_render.hostname if parsed_render else None
render_origin = f"{parsed_render.scheme}://{parsed_render.hostname}" if parsed_render else None

# ===========================
# Hosts / CSRF
# ===========================
# 1) Pega das variáveis, se existirem
ALLOWED_HOSTS = [h for h in env.list("ALLOWED_HOSTS", default=[]) if h]
CSRF_TRUSTED_ORIGINS = [o for o in env.list("CSRF_TRUSTED_ORIGINS", default=[]) if o]

# 2) Completa automaticamente para Render, se não informado
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

# 3) Em dev, garante localhost
if DEBUG:
    for h in ["127.0.0.1", "localhost"]:
        if h not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(h)

# 4) CSRF origins
if render_origin and render_origin not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(render_origin)
# compat: qualquer *.onrender.com
if "https://*.onrender.com" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ===========================
# Apps
# ===========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    "cloudinary",
    'core.apps.CoreConfig',
    "cloudinary_storage"
    ]

# ===========================
# Middleware
# ===========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "arutourism.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.search_filters",
            ],
        },
    },
]

WSGI_APPLICATION = "arutourism.wsgi.application"

# ===========================
# Database (SQLite dev / PG prod)
# ===========================
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# ===========================
# Password validators
# ===========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===========================
# Locale
# ===========================
LANGUAGE_CODE = "pt-BR"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ===========================
# Static (Whitenoise)
# ===========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Se tiver pasta 'static' dentro do projeto, descomente:
STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ===========================
# Auth redirects
# ===========================
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# ===========================
# Media (local dev / Cloudinary prod se configurado)
# ===========================
cloud_name = env("CLOUDINARY_CLOUD_NAME", default="")
api_key = env("CLOUDINARY_API_KEY", default="")
api_secret = env("CLOUDINARY_API_SECRET", default="")

if not DEBUG and cloud_name and api_key and api_secret:
    import cloudinary
    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

    # ⚠️ Não force MEDIA_URL para Cloudinary; deixe o storage gerar a URL absoluta
    # MEDIA_URL = f"https://res.cloudinary.com/{cloud_name}/image/upload/"  # REMOVER

    # Opcionalmente deixe sem definir, ou mantenha algo neutro:
    MEDIA_URL = "/media/"   # neutro; não será usado para .url do FileField
else:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# ===========================
# E-mail (SMTP real em prod; console em dev)
# ===========================
EMAIL_ENABLED = env.bool("EMAIL_ENABLED", default=IS_PROD)

if EMAIL_ENABLED:
    EMAIL_BACKEND   = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST      = env("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT      = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS   = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL   = env.bool("EMAIL_USE_SSL", default=False)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    # Remetente padrão: use endereço verificado no provedor (p/ Gmail, o mesmo da conta)
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "no-reply@localhost")
    SERVER_EMAIL       = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

    # Sem credenciais → cai p/ console (evita quebrar deploy)
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND       = "django.core.mail.backends.console.EmailBackend"
        DEFAULT_FROM_EMAIL  = "no-reply@localhost"
        SERVER_EMAIL        = "server@localhost"
else:
    EMAIL_BACKEND      = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = "no-reply@localhost"
    SERVER_EMAIL       = "server@localhost"

EMAIL_TIMEOUT = 20

# ===========================
# Links absolutos (e-mail)
# ===========================
if render_host and not DEBUG:
    DEFAULT_DOMAIN = env("DEFAULT_DOMAIN", default=render_host)
    DEFAULT_PROTOCOL = env("DEFAULT_PROTOCOL", default="https")
else:
    DEFAULT_DOMAIN = env("DEFAULT_DOMAIN", default="127.0.0.1:8000")
    DEFAULT_PROTOCOL = env("DEFAULT_PROTOCOL", default="http")

# Tempo de validade do link de reset (24h)
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

# ===========================
# Segurança (só em produção)
# ===========================
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"

# ===========================
# Modo testes (evita erro de manifest)
# ===========================
TESTING = "test" in sys.argv
if TESTING:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {  # erros de requests (500) vão aqui
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

WHITENOISE_MANIFEST_STRICT = False