"""
GovAlert Django Settings — Base (Phase 1)
₦0/month architecture: SQLite + APScheduler + Telegram channels.
No PostgreSQL, no Redis, no Celery required.
"""
from pathlib import Path
from decouple import config, Csv
import sys

# Detect if we are running unit/integration tests
TESTING = 'test' in sys.argv or 'pytest' in sys.modules or any('pytest' in arg for arg in sys.argv)

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-temp-key-for-collectstatic')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# ─── Applications ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_apscheduler',   # Phase 1 scheduler — no Redis needed

    # Project apps
    'apps.accounts.apps.AccountsConfig',
    'apps.agencies',
    'apps.monitor.apps.MonitorConfig',
    'apps.detector',
    'apps.alerts',
    'apps.subscriptions',
    'apps.notifications',
    'apps.bot',
    'apps.api',
]

# ─── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ─── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ─── Database — Phase 1: SQLite ────────────────────────────────────────────────
# Single file, no server, no cost.
# Phase 2: change ENGINE to postgresql and update remaining keys.
#
# WAL mode: Allows concurrent reads alongside a single write, massively reducing
# "database is locked" errors from APScheduler running multiple executor threads.
# busy_timeout: If a write is blocked, wait up to 5s before raising an error
# instead of failing immediately (default behaviour).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'users.db',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

# ─── Cache — Phase 1: Local Memory ─────────────────────────────────────────────
# No Redis needed. LocMemCache is per-process — fine for single-server MVP.
# Phase 2: Switch to django_redis.cache.RedisCache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'govalert-cache',
    }
}

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─── Sessions ──────────────────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Stored in SQLite

# ─── DRF ──────────────────────────────────────────────────────────────────
# Public endpoints (agencies, jobs, status) use AllowAny — no auth needed.
# Admin and user-specific endpoints declare their own permission_classes.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ─── JWT ───────────────────────────────────────────────────────────────────────
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─── CORS ─────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=','.join([
        'http://localhost:3000',
        'http://localhost:8081',
        'https://govalert-henna.vercel.app',
    ]),
    cast=Csv()
)
CORS_ALLOWED_ORIGIN_REGEXES = [
    # Matches all Vercel preview URLs: https://govalert-*.vercel.app
    r'^https://govalert-[a-z0-9-]+\.vercel\.app$',
]
CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = config('FRONTEND_URL', default='https://govalert-henna.vercel.app')

# ─── Static & Media ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── APScheduler ───────────────────────────────────────────────────────────────
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # seconds

# ─── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'apps': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'apscheduler': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# ─── Telegram Bot ──────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_WEBHOOK_SECRET = config('TELEGRAM_WEBHOOK_SECRET', default='')
TELEGRAM_WEBHOOK_URL = config('TELEGRAM_WEBHOOK_URL', default='')
SUPER_ADMIN_TELEGRAM_IDS = config('SUPER_ADMIN_TELEGRAM_IDS', default='', cast=Csv(cast=int))

# ─── Telegram Channels (Phase 1 Storage) ───────────────────────────────────────
# Private channel for event log (one JSON message per recruitment event)
TELEGRAM_EVENTS_CHANNEL_ID = config('TELEGRAM_EVENTS_CHANNEL_ID', default='')
# Public channel for human-readable alert feed
TELEGRAM_PUBLIC_CHANNEL_ID = config('TELEGRAM_PUBLIC_CHANNEL_ID', default='')
# Private channel for nightly SQLite backup
TELEGRAM_BACKUP_CHANNEL_ID = config('TELEGRAM_BACKUP_CHANNEL_ID', default='')

# ─── Gemini AI ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_MODEL = 'gemini-1.5-flash'
GEMINI_MAX_CALLS_PER_MINUTE = 60

# ─── GovAlert App Settings ─────────────────────────────────────────────────────
PORTAL_CHECK_INTERVAL_MINUTES = 20
PORTAL_CHECK_INTERVAL_HIGH_PRIORITY = 5
PORTAL_CHECK_INTERVAL_LOW_ACTIVITY = 60
MAX_PLAYWRIGHT_INSTANCES = 3
ALERT_DEDUP_WINDOW_HOURS = 24
MAX_USER_HISTORY_DISPLAY = 20
SCRAPER_REQUEST_DELAY_MIN = 2
SCRAPER_REQUEST_DELAY_MAX = 8
TRUST_SCORE_SEND_THRESHOLD = 50
TRUST_SCORE_ADMIN_REVIEW_THRESHOLD = 30
TRUST_SCORE_FAKE_THRESHOLD = 29
TELEGRAM_RATE_LIMIT_PER_SECOND = 30
TELEGRAM_RATE_LIMIT_PER_USER = 1

# ─── Local Config File Paths ────────────────────────────────────────────────────
# JSON config files — static data that rarely changes
PORTALS_JSON_PATH = BASE_DIR / 'config' / 'portals.json'
AGENCIES_JSON_PATH = BASE_DIR / 'config' / 'agencies.json'
INDEX_JSON_PATH = BASE_DIR / 'config' / 'index.json'

# ─── Storage Abstraction ───────────────────────────────────────────────────────
STORAGE_BACKEND = config('STORAGE_BACKEND', default='core.storage.DjangoORMStorageBackend')
