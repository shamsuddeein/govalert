import os
import sys
from django.apps import AppConfig

class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitor'

    def ready(self):
        # To avoid running scheduler twice in dev (reloader) or during migrations/commands
        # Only start scheduler when running the main web server
        # Django runserver sets RUN_MAIN='true' for the execution reload.
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
