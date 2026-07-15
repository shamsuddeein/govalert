import os
import sys
from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitor'

    def ready(self):
        # ── SQLite WAL mode ────────────────────────────────────────────────────
        # Applies WAL journal mode to every SQLite connection created in this
        # process. WAL allows concurrent reads + 1 write without blocking,
        # which reduces the "database is locked" warnings from APScheduler
        # executor threads writing simultaneously.
        # This is the correct Django approach (init_command is MySQL-only).
        self._configure_sqlite_wal()

        # ── Scheduler ─────────────────────────────────────────────────────────
        # Check if we are running unit/integration tests
        is_testing = (
            'test' in sys.argv or
            any('pytest' in arg for arg in sys.argv) or
            'pytest' in sys.modules
        )
        if is_testing:
            return

        # To avoid running scheduler twice in dev (reloader) or during
        # migrations/commands, only start scheduler when running the main
        # web server. Django runserver sets RUN_MAIN='true' for the reloader.
        is_manage_py = any(arg.endswith('manage.py') for arg in sys.argv)
        is_runserver = 'runserver' in sys.argv

        if is_manage_py and is_runserver:
            if os.environ.get('RUN_MAIN') == 'true':
                from config import scheduler
                scheduler.start()
        elif not is_manage_py:
            # Running under ASGI/WSGI (production)
            from config import scheduler
            scheduler.start()

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
