FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    # Playwright dependencies
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN mkdir -p /app/logs
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/production.txt
RUN playwright install chromium
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD python manage.py migrate --noinput && python manage.py load_ng_portals && gunicorn config.wsgi:application -w 2 -b 0.0.0.0:8000
