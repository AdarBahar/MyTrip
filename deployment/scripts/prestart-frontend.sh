#!/bin/bash

# Frontend Pre-start Script
# Runs before the frontend service starts to ensure everything is ready

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

# Ensure log directory exists
mkdir -p "$LOG_DIR"
chown www-data:www-data "$LOG_DIR"

# Check if build exists
if [ ! -d "$APP_DIR/frontend/.next" ]; then
    log_error "Frontend build not found. Run 'pnpm build' first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "$APP_DIR/frontend/node_modules" ]; then
    log_error "Frontend dependencies not installed. Run 'pnpm install' first."
    exit 1
fi

# Check if backend is running
log_info "Checking backend connectivity..."
backend_url="http://127.0.0.1:8000/health"
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f "$backend_url" > /dev/null 2>&1; then
        log_info "Backend is running and healthy"
        break
    else
        if [ $attempt -eq $max_attempts ]; then
            log_error "Backend is not responding after $max_attempts attempts"
            exit 1
        fi
        log_info "Waiting for backend to be ready... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    fi
done

log_info "Frontend pre-start checks completed successfully"
