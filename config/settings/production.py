"""
GovAlert Django Settings — Production (Phase 1)
Free-tier deployment: Railway / Render / fly.io
Still SQLite — no PostgreSQL needed until Phase 2.
"""
from .base import *  # noqa

DEBUG = False

# ─── Security Headers ──────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# ─── Logging — Production ──────────────────────────────────────────────────────
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': str(BASE_DIR / 'logs' / 'govalert.log'),
    'maxBytes': 10 * 1024 * 1024,  # 10 MB
    'backupCount': 5,
    'formatter': 'verbose',
}
LOGGING['root']['handlers'] = ['console', 'file']

# ─── Phase 2 upgrade hints (commented out — uncomment when ready) ──────────────
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': config('REDIS_URL'),
#     }
# }
