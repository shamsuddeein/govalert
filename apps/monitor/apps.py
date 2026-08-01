import os
import sys
from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitor'

    def ready(self):
        # ── SQLite WAL mode ────────────────────────────────────────────────────
        # Applies WAL journal mode to every SQLite connection created in this
        # process. WAL allows concurrent reads + 1 write without blocking.
        # This is a no-op on PostgreSQL (connection_created fires but the
        # vendor check ensures it only runs for SQLite).
        self._configure_sqlite_wal()

        # ── Scheduler ─────────────────────────────────────────────────────────
        # APScheduler is now a dedicated Railway worker process (worker.py).
        # It must NOT start inside the web (gunicorn) process to avoid:
        #   - Jobs running twice (one per gunicorn worker).
        #   - Lost jobs on Railway dyno restarts.
        #   - Resource contention between HTTP traffic and scraping threads.
        #
        # The web process simply sets DISABLE_IN_PROCESS_SCHEDULER=true (or
        # USE_CELERY=true) and never touches APScheduler at all.
        #
        # If neither flag is set AND we are in a plain `runserver` (local dev
        # without the dedicated worker), fall back to the in-process scheduler
        # so developers still get scheduled jobs locally.
        self._maybe_start_dev_scheduler()

    def _maybe_start_dev_scheduler(self):
        """Start the in-process scheduler only for local `runserver` dev sessions."""
        # Skip in test runners.
        is_testing = (
            'test' in sys.argv or
            any('pytest' in arg for arg in sys.argv) or
            'pytest' in sys.modules
        )
        if is_testing:
            return

        from django.conf import settings

        # Explicit opt-out: worker.py is handling scheduling.
        if getattr(settings, 'DISABLE_IN_PROCESS_SCHEDULER', False):
            return

        # Celery-based scheduling is active — skip APScheduler.
        if getattr(settings, 'USE_CELERY', False):
            return

        # Only start for `manage.py runserver` (not gunicorn / uvicorn).
        is_runserver = any(arg.endswith('manage.py') for arg in sys.argv) and 'runserver' in sys.argv
        if not is_runserver:
            return

        # Django runserver spawns a reloader child; only start in that child.
        if os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from config import scheduler
            scheduler.start()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Could not start background scheduler in dev: %s", exc
            )

    @staticmethod
    def _configure_sqlite_wal():
        """Enable WAL mode and a busy_timeout for all SQLite connections."""
        from django.db.backends.signals import connection_created

        def _set_wal(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                cursor = connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL;')
                cursor.execute('PRAGMA busy_timeout=5000;')

        connection_created.connect(_set_wal)
