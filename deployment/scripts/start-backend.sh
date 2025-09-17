#!/bin/bash

# Production Backend Startup Script
# Starts the FastAPI backend with production settings

set -e

# Configuration
APP_DIR="/opt/dayplanner"
LOG_DIR="/var/log/dayplanner"

# Load environment variables
if [ -f "$APP_DIR/.env.production" ]; then
    export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
else
    echo "Error: Production environment file not found: $APP_DIR/.env.production"
    exit 1
fi

# Set defaults
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
BACKEND_PORT=${BACKEND_PORT:-8000}
BACKEND_WORKERS=${BACKEND_WORKERS:-4}

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Change to backend directory
cd "$APP_DIR/backend"

# Activate virtual environment
source venv/bin/activate

# Start the backend with production settings
exec uvicorn app.main:app \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT" \
    --workers "$BACKEND_WORKERS" \
    --access-log \
    --access-logfile "$LOG_DIR/backend-access.log" \
    --log-level info \
    --no-use-colors \
    --loop uvloop \
    --http httptools
