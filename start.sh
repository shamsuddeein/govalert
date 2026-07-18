#!/bin/bash
# start.sh — Starts the GovAlert local development server in the background

# Navigate to the project root directory
cd "$(dirname "$0")"

# Check if already running
if [ -f "runserver.pid" ]; then
    PID=$(cat runserver.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "GovAlert is already running (PID $PID)."
        exit 1
    else
        rm runserver.pid
    fi
fi

# Check if virtual environment exists and activate
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Running with global python."
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Register bot commands
echo "Registering Telegram bot commands..."
python manage.py register_bot_commands

# Load portals
echo "Loading official recruitment portals..."
python manage.py load_ng_portals

# Start Django development server in the background
echo "Starting Django development server on port 8000..."
nohup python manage.py runserver 0.0.0.0:8000 > runserver.log 2>&1 &
PID=$!

# Save process ID
echo $PID > runserver.pid
echo "GovAlert started in background with PID $PID."
echo "Logs are being written to runserver.log"

# Clean up old celery pids
rm -f celery.pids

# Start Celery workers and beat
echo "Starting Celery workers (monitoring, notifications, ai)..."
nohup celery -A config worker -Q monitoring -c 4 -n monitor@%h --loglevel=info > celery_monitor.log 2>&1 &
echo $! >> celery.pids

nohup celery -A config worker -Q notifications -c 8 -n notify@%h --loglevel=info > celery_notifications.log 2>&1 &
echo $! >> celery.pids

nohup celery -A config worker -Q ai -c 2 -n ai@%h --loglevel=info > celery_ai.log 2>&1 &
echo $! >> celery.pids

echo "Starting Celery beat..."
nohup celery -A config beat -l info > celery_beat.log 2>&1 &
echo $! >> celery.pids

echo "Celery services started. PIDs saved to celery.pids"

