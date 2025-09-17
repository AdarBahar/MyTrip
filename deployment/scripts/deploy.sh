#!/bin/bash

# DayPlanner Production Deployment Script
# This script deploys the application to production without Docker

set -e

# Configuration
APP_DIR="/opt/dayplanner"
BACKUP_DIR="/opt/dayplanner-backups"
LOG_DIR="/var/log/dayplanner"
NGINX_SITES="/etc/nginx/sites-available"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set proper ownership
    chown -R www-data:www-data "$APP_DIR"
    chown -R www-data:www-data "$LOG_DIR"
    
    log_success "Directories created"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        nginx \
        curl \
        git \
        build-essential \
        libpq-dev \
        mysql-client
    
    # Install pnpm globally
    npm install -g pnpm
    
    log_success "System dependencies installed"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd "$APP_DIR/backend"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set proper ownership
    chown -R www-data:www-data venv/
    
    log_success "Python environment setup complete"
}

# Build frontend
build_frontend() {
    log_info "Building frontend for production..."
    
    cd "$APP_DIR/frontend"
    
    # Install dependencies
    sudo -u www-data pnpm install
    
    # Build for production
    sudo -u www-data pnpm build
    
    log_success "Frontend build complete"
}

# Setup systemd services
setup_services() {
    log_info "Setting up systemd services..."
    
    # Copy service files
    cp "$APP_DIR/deployment/systemd/dayplanner-backend.service" "$SYSTEMD_DIR/"
    cp "$APP_DIR/deployment/systemd/dayplanner-frontend.service" "$SYSTEMD_DIR/"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable dayplanner-backend.service
    systemctl enable dayplanner-frontend.service
    
    log_success "Systemd services configured"
}

# Setup nginx
setup_nginx() {
    log_info "Setting up Nginx configuration..."
    
    # Copy nginx config
    cp "$APP_DIR/deployment/nginx/dayplanner.conf" "$NGINX_SITES/"
    
    # Enable site
    ln -sf "$NGINX_SITES/dayplanner.conf" /etc/nginx/sites-enabled/
    
    # Test nginx config
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    log_success "Nginx configuration complete"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Load environment
    export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
    
    # Run migrations
    alembic upgrade head
    
    log_success "Database migrations complete"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start backend
    systemctl start dayplanner-backend.service
    
    # Wait a moment for backend to start
    sleep 5
    
    # Start frontend
    systemctl start dayplanner-frontend.service
    
    # Check status
    systemctl status dayplanner-backend.service --no-pager
    systemctl status dayplanner-frontend.service --no-pager
    
    log_success "Services started"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check frontend
    if curl -f http://localhost:3500 > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Main deployment function
main() {
    log_info "Starting DayPlanner production deployment..."
    
    check_root
    create_directories
    install_dependencies
    setup_python_env
    build_frontend
    setup_services
    setup_nginx
    run_migrations
    start_services
    health_check
    
    log_success "Deployment completed successfully!"
    log_info "Application is now running at:"
    log_info "  Frontend: http://localhost (via Nginx)"
    log_info "  Backend API: http://localhost/api"
    log_info "  Direct Backend: http://localhost:8000"
    log_info ""
    log_info "Service management commands:"
    log_info "  sudo systemctl status dayplanner-backend"
    log_info "  sudo systemctl status dayplanner-frontend"
    log_info "  sudo systemctl restart dayplanner-backend"
    log_info "  sudo systemctl restart dayplanner-frontend"
}

# Run deployment
main "$@"
