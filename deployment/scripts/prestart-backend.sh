#!/bin/bash

# Backend Pre-start Script
# Runs before the backend service starts to ensure everything is ready

set -e

# Configuration
APP_DIR="/opt/dayplanner"
LOG_DIR="/var/log/dayplanner"

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2
}

# Check if environment file exists
if [ ! -f "$APP_DIR/.env.production" ]; then
    log_error "Production environment file not found: $APP_DIR/.env.production"
    exit 1
fi

# Load environment variables
export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)

# Check required environment variables
required_vars=("DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD" "APP_SECRET")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done

# Ensure log directory exists
mkdir -p "$LOG_DIR"
chown www-data:www-data "$LOG_DIR"

# Check database connectivity
log_info "Checking database connectivity..."
cd "$APP_DIR/backend"
source venv/bin/activate

# Run the prestart check
python prestart.py

if [ $? -eq 0 ]; then
    log_info "Database connectivity check passed"
else
    log_error "Database connectivity check failed"
    exit 1
fi

# Check if virtual environment is properly set up
if [ ! -f "$APP_DIR/backend/venv/bin/uvicorn" ]; then
    log_error "Backend virtual environment not properly set up"
    exit 1
fi

log_info "Backend pre-start checks completed successfully"
