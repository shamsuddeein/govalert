FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    # Playwright dependencies
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt
RUN playwright install chromium
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
