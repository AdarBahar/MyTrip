#!/bin/bash

# Production Update Script
# Updates the application from Git repository

set -e

# Configuration
APP_DIR="/opt/dayplanner"
BACKUP_DIR="/opt/dayplanner-backups"
LOG_DIR="/var/log/dayplanner"

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

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    systemctl stop dayplanner-frontend.service || true
    systemctl stop dayplanner-backend.service || true
    
    log_success "Services stopped"
}

# Create backup of current deployment
backup_current() {
    log_info "Creating backup of current deployment..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_path="$BACKUP_DIR/deployment_$timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup application code (excluding node_modules and venv)
    rsync -av --exclude='node_modules' --exclude='venv' --exclude='.git' \
          "$APP_DIR/" "$backup_path/"
    
    log_success "Backup created at: $backup_path"
}

# Update code from Git
update_code() {
    log_info "Updating code from Git repository..."
    
    cd "$APP_DIR"
    
    # Fetch latest changes
    git fetch origin
    
    # Show what will be updated
    log_info "Changes to be applied:"
    git log --oneline HEAD..origin/main
    
    # Ask for confirmation in interactive mode
    if [ -t 0 ]; then
        read -p "Do you want to proceed with the update? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "Update cancelled by user"
            exit 0
        fi
    fi
    
    # Pull latest changes
    git pull origin main
    
    log_success "Code updated successfully"
}

# Update backend dependencies
update_backend() {
    log_info "Updating backend dependencies..."
    
    cd "$APP_DIR/backend"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update pip
    pip install --upgrade pip
    
    # Install/update dependencies
    pip install -r requirements.txt
    
    # Set proper ownership
    chown -R www-data:www-data venv/
    
    log_success "Backend dependencies updated"
}

# Update frontend dependencies and rebuild
update_frontend() {
    log_info "Updating frontend dependencies and rebuilding..."
    
    cd "$APP_DIR/frontend"
    
    # Update dependencies
    sudo -u www-data pnpm install
    
    # Rebuild for production
    sudo -u www-data pnpm build
    
    log_success "Frontend updated and rebuilt"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Use the migration script
    "$APP_DIR/deployment/scripts/migrate.sh"
    
    log_success "Database migrations completed"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start backend first
    systemctl start dayplanner-backend.service
    
    # Wait for backend to be ready
    sleep 10
    
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
    
    # Wait for services to fully start
    sleep 15
    
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

# Rollback function
rollback() {
    log_error "Update failed. Rolling back..."
    
    # Find the latest backup
    latest_backup=$(ls -t "$BACKUP_DIR"/deployment_* | head -n1)
    
    if [ -n "$latest_backup" ]; then
        log_info "Rolling back to: $latest_backup"
        
        # Stop services
        systemctl stop dayplanner-frontend.service || true
        systemctl stop dayplanner-backend.service || true
        
        # Restore from backup
        rsync -av --delete "$latest_backup/" "$APP_DIR/"
        
        # Restore ownership
        chown -R www-data:www-data "$APP_DIR"
        
        # Start services
        systemctl start dayplanner-backend.service
        sleep 10
        systemctl start dayplanner-frontend.service
        
        log_success "Rollback completed"
    else
        log_error "No backup found for rollback"
    fi
}

# Main update function
main() {
    log_info "Starting production update process..."
    
    # Set up error handling for rollback
    trap rollback ERR
    
    check_root
    stop_services
    backup_current
    update_code
    update_backend
    update_frontend
    run_migrations
    start_services
    health_check
    
    # Disable rollback trap on success
    trap - ERR
    
    log_success "Update completed successfully!"
    log_info "Application is now running the latest version"
    log_info "Backup location: $BACKUP_DIR"
}

# Handle script arguments
case "${1:-}" in
    --rollback)
        log_info "Manual rollback requested"
        rollback
        ;;
    --help)
        echo "Usage: $0 [--rollback|--help]"
        echo "  --rollback  Rollback to the previous deployment"
        echo "  --help      Show this help message"
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
