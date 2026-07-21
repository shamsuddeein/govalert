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

# ─── Security — read from env, with build-safe default for static collection step
SECRET_KEY = config('SECRET_KEY', default='django-insecure-build-time-placeholder-do-not-use-in-prod')
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
    'django_apscheduler',   # Phase 1 scheduler
    'django_celery_beat',   # Phase 2 scheduler
    'django_celery_results', # Celery results stored in DB

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

# ─── Database ──────────────────────────────────────────────────────────────────
import dj_database_url

default_sqlite_url = f"sqlite:///{BASE_DIR / 'users.db'}"

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=default_sqlite_url),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ─── Cache ─────────────────────────────────────────────────────────────────────
redis_url = config('REDIS_URL', default='')
if redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─── Sessions ──────────────────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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
    # Rate limiting: 60 requests/minute for anonymous callers.
    # Prevents API scraping and abuse of the public endpoints.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '300/min',
    },
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
        'http://localhost:8080',
        'http://localhost:8081',
        'https://recruitmentalert.com.ng',
        'https://www.recruitmentalert.com.ng',
        'https://govalert-henna.vercel.app',
    ]),
    cast=Csv()
)
# IMPORTANT: Do not add CORS_ALLOWED_ORIGIN_REGEXES with CORS_ALLOW_CREDENTIALS=True.
# A wildcard regex allows any Vercel preview deploy to make credentialed requests.
# To allow specific preview URLs, add them explicitly to CORS_ALLOWED_ORIGINS via env var.
CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = config('FRONTEND_URL', default='https://www.recruitmentalert.com.ng')

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
TELEGRAM_BOT_USERNAME = config('TELEGRAM_BOT_USERNAME', default='govalerts_bot')
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

# ─── OpenAI & AI Intelligence ───────────────────────────────────────────────────
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-5.6')

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

# ─── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_ROUTES = {
    'apps.monitor.tasks.check_high_priority_portals': {'queue': 'monitoring'},
    'apps.monitor.tasks.check_standard_portals': {'queue': 'monitoring'},
    'apps.monitor.tasks.check_low_activity_portals': {'queue': 'monitoring'},
    'apps.monitor.tasks.portal_check': {'queue': 'monitoring'},
    'apps.notifications.tasks.dispatch_alert': {'queue': 'notifications'},
    'apps.notifications.tasks.retry_failed_notifications': {'queue': 'notifications'},
}
USE_CELERY = True

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'check_high_priority_portals': {
        'task': 'apps.monitor.tasks.check_high_priority_portals',
        'schedule': timedelta(minutes=PORTAL_CHECK_INTERVAL_HIGH_PRIORITY),
    },
    'check_standard_portals': {
        'task': 'apps.monitor.tasks.check_standard_portals',
        'schedule': timedelta(minutes=PORTAL_CHECK_INTERVAL_MINUTES),
    },
    'check_low_activity_portals': {
        'task': 'apps.monitor.tasks.check_low_activity_portals',
        'schedule': timedelta(minutes=PORTAL_CHECK_INTERVAL_LOW_ACTIVITY),
    },
    'retry_failed_notifications': {
        'task': 'apps.notifications.tasks.retry_failed_notifications',
        'schedule': timedelta(hours=1),
    },
    'nightly_backup': {
        'task': 'apps.monitor.tasks.nightly_backup',
        'schedule': crontab(hour=1, minute=0),
    },
    'daily_health_report': {
        'task': 'apps.monitor.tasks.daily_health_report',
        'schedule': crontab(hour=8, minute=0),
    },
    'cleanup_inactive_users': {
        'task': 'apps.accounts.tasks.cleanup_inactive_users',
        'schedule': timedelta(hours=24),
    },
    # Aggregate yesterday's Snapshots into PortalHealthLog. Runs at 00:30 so
    # yesterday's data is fully complete before aggregation begins.
    'aggregate_portal_health_logs': {
        'task': 'apps.monitor.tasks.aggregate_portal_health_logs',
        'schedule': crontab(hour=0, minute=30),
    },
    # Purge raw_content from Snapshots >30 days old to control DB size.
    # Rows are retained (hash + status preserved), only page text is cleared.
    'purge_old_snapshot_content': {
        'task': 'apps.monitor.tasks.purge_old_snapshot_content',
        'schedule': crontab(hour=3, minute=0),
    },
}


