"""
GovAlert Django Settings — Development
DEBUG mode. SQLite fallback optional. No S3.
"""
from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += [
    'django_extensions',
    'silk',
]

MIDDLEWARE += [
    'silk.middleware.SilkyMiddleware',
]

# ─── Dev Email (console backend) ───────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── Django Silk profiling ─────────────────────────────────────────────────────
SILKY_PYTHON_PROFILER = True
SILKY_MAX_RECORDED_REQUESTS = 100

# ─── Internal IPs (Django Debug Toolbar) ──────────────────────────────────────
INTERNAL_IPS = ['127.0.0.1']

# ─── Disable Silk in tests ─────────────────────────────────────────────────────
SILKY_ENABLED = False
