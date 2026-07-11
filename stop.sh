#!/bin/bash
# stop.sh — Stops the GovAlert local development server

# Navigate to the project root directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "runserver.pid" ]; then
    PID=$(cat runserver.pid)
    echo "Stopping GovAlert (PID $PID)..."
    kill $PID 2>/dev/null
    
    # Give it a moment to shut down gracefully
    sleep 1
    if ps -p $PID > /dev/null 2>&1; then
        echo "Process did not stop, forcing termination..."
        kill -9 $PID 2>/dev/null
    fi
    rm runserver.pid
fi

# Clean up any remaining Django runserver processes
pids=$(pgrep -f "manage.py runserver")
if [ ! -z "$pids" ]; then
    echo "Stopping remaining Django development server processes (PIDs: $pids)..."
    kill $pids 2>/dev/null
    sleep 1
    kill -9 $pids 2>/dev/null
fi

echo "GovAlert stopped successfully."
