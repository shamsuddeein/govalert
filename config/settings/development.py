"""
GovAlert Django Settings — Development
DEBUG mode. Uses SQLite (same as production in Phase 1).
"""
from .base import *  # noqa

DEBUG = True

# ─── Dev Email ─────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── Allow all hosts & CORS origins in dev ─────────────────────────────────────
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

