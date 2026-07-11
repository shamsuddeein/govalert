from django.apps import AppConfig
from django.db.backends.signals import connection_created

def activate_sqlite_pragmas(sender, connection, **kwargs):
    """Enable WAL mode, foreign keys, and synchronous NORMAL on SQLite connections."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.execute('PRAGMA cache_size=-32000;')  # 32MB cache

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        connection_created.connect(activate_sqlite_pragmas)
