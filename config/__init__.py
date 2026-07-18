"""
GovAlert config package.
Phase 2: Celery and Redis configured.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
