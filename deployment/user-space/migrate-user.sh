#!/bin/bash

# User-Space Database Migration Script
# Runs database migrations without root access

set -e

# Configuration
APP_DIR="$HOME/dayplanner"
BACKUP_DIR="$HOME/dayplanner-backups"
LOG_DIR="$HOME/dayplanner/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_DIR/migration.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$LOG_DIR/migration.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" >> "$LOG_DIR/migration.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_DIR/migration.log"
}

# Load environment variables
load_environment() {
    if [ ! -f "$APP_DIR/.env.production" ]; then
        log_error "Production environment file not found: $APP_DIR/.env.production"
        exit 1
    fi
    
    export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
    log_info "Environment variables loaded"
}

# Create backup of current database
backup_database() {
    log_info "Creating database backup..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename with timestamp
    backup_file="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Create database backup
    mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log_success "Database backup created: $backup_file"
        # Compress the backup
        gzip "$backup_file"
        log_success "Backup compressed: ${backup_file}.gz"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Run the prestart check
    python prestart.py
    
    if [ $? -eq 0 ]; then
        log_success "Database connectivity check passed"
    else
        log_error "Database connectivity check failed"
        exit 1
    fi
}

# Show current migration status
show_migration_status() {
    log_info "Current migration status:"
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    alembic current
    alembic history --verbose
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Show what migrations will be applied
    log_info "Migrations to be applied:"
    alembic upgrade head --sql
    
    # Ask for confirmation in interactive mode
    if [ -t 0 ]; then
        read -p "Do you want to proceed with these migrations? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "Migration cancelled by user"
            exit 0
        fi
    fi
    
    # Apply migrations
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Restart services after migration
restart_services() {
    log_info "Restarting services..."
    
    # Source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    # Check if PM2 is running
    if pm2 list | grep -q "dayplanner"; then
        pm2 restart all
        log_success "Services restarted with PM2"
    else
        log_warning "PM2 services not running"
    fi
}

# Health check after migration
health_check() {
    log_info "Performing post-migration health check..."
    
    # Wait for services to start
    sleep 10
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    log_success "Post-migration health check passed"
}

# Main migration function
main() {
    log_info "Starting database migration process..."
    
    # Ensure log directory exists
    mkdir -p "$LOG_DIR"
    
    load_environment
    check_database
    show_migration_status
    backup_database
    run_migrations
    restart_services
    health_check
    
    log_success "Database migration completed successfully!"
    log_info "Backup location: $BACKUP_DIR"
    log_info "Migration log: $LOG_DIR/migration.log"
}

# Handle script arguments
case "${1:-}" in
    --dry-run)
        log_info "Dry run mode - showing migrations without applying"
        load_environment
        cd "$APP_DIR/backend"
        source venv/bin/activate
        alembic upgrade head --sql
        ;;
    --status)
        log_info "Showing current migration status"
        load_environment
        show_migration_status
        ;;
    --help)
        echo "Usage: $0 [--dry-run|--status|--help]"
        echo "  --dry-run  Show migrations without applying them"
        echo "  --status   Show current migration status"
        echo "  --help     Show this help message"
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
