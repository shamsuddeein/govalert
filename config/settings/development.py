"""
GovAlert Django Settings — Development
DEBUG mode. Uses SQLite (same as production in Phase 1).
"""
from .base import *  # noqa

DEBUG = True

# ─── Dev Email ─────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── Allow all hosts in dev ────────────────────────────────────────────────────
ALLOWED_HOSTS = ['*']
