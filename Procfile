web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && DISABLE_IN_PROCESS_SCHEDULER=true gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
worker: python worker.py
