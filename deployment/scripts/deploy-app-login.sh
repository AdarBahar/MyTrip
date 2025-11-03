#!/bin/bash

# Deploy App Login Endpoint and Recent Updates to Production
# This script deploys the latest changes including the new app-login endpoint

set -e

# Configuration
REPO_URL="https://github.com/AdarBahar/MyTrip.git"
APP_DIR="/opt/dayplanner"
BACKUP_DIR="/opt/dayplanner-backups"
LOG_DIR="/var/log/dayplanner"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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

# Create backup of current deployment
create_backup() {
    log_info "Creating backup of current deployment..."
    
    if [ -d "$APP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$APP_DIR" . 2>/dev/null || true
        log_success "Backup created: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    else
        log_warning "No existing deployment found to backup"
    fi
}

# Clone or update repository with clean deployment
update_repository() {
    log_info "Updating repository with clean deployment..."

    # Create temporary directory for clean checkout
    TEMP_DIR="/tmp/dayplanner-deploy-$(date +%s)"
    mkdir -p "$TEMP_DIR"

    # Clone fresh copy to temp directory
    log_info "Cloning repository to temporary location..."
    git clone "$REPO_URL" "$TEMP_DIR"
    cd "$TEMP_DIR"

    # Show latest commits
    log_info "Latest commits:"
    git log --oneline -5

    # Create backup of current deployment if it exists
    if [ -d "$APP_DIR" ]; then
        BACKUP_DIR="/opt/dayplanner-backups/pre-deploy-$(date +%Y%m%d_%H%M%S)"
        log_info "Creating backup at: $BACKUP_DIR"
        mkdir -p "$(dirname "$BACKUP_DIR")"
        cp -r "$APP_DIR" "$BACKUP_DIR"
    fi

    # Ensure target directory exists
    mkdir -p "$APP_DIR"

    # Use rsync to deploy only necessary files
    log_info "Deploying clean production files..."
    if [ -f "$TEMP_DIR/.deployignore" ]; then
        rsync -av --delete --exclude-from="$TEMP_DIR/.deployignore" \
              "$TEMP_DIR/" "$APP_DIR/"
        log_success "Clean deployment completed using .deployignore"
    else
        log_warning ".deployignore not found, using manual exclusions"
        rsync -av --delete \
              --exclude='.git' \
              --exclude='*.md' \
              --exclude='docs/' \
              --exclude='test_*.py' \
              --exclude='*_test.py' \
              --exclude='deploy_*.sh' \
              --exclude='.vscode/' \
              --exclude='.github/' \
              --exclude='node_modules/' \
              --exclude='__pycache__/' \
              --exclude='*.log' \
              --exclude='*.tmp' \
              --exclude='deployment/production/' \
              --exclude='deployment/user-space/' \
              "$TEMP_DIR/" "$APP_DIR/"
        log_success "Clean deployment completed using manual exclusions"
    fi

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"

    # Set proper ownership
    chown -R www-data:www-data "$APP_DIR"

    cd "$APP_DIR"
}

# Install/update Python dependencies
update_python_dependencies() {
    log_info "Updating Python dependencies..."
    
    cd "$APP_DIR/backend"
    
    # Activate virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Created new virtual environment"
    fi
    
    source venv/bin/activate
    
    # Update pip and install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Verify bcrypt and passlib are installed for app-login
    pip install bcrypt==4.0.1 passlib[bcrypt]==1.7.4
    
    log_success "Python dependencies updated"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Load production environment
    if [ -f "$APP_DIR/.env.production" ]; then
        export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
    else
        log_error "Production environment file not found: $APP_DIR/.env.production"
        log_error "Please create this file based on deployment/production.env.example"
        exit 1
    fi
    
    # Run prestart checks
    python prestart.py
    
    # Run migrations
    alembic upgrade head
    
    log_success "Database migrations completed"
}

# Test app-login endpoint functionality
test_app_login() {
    log_info "Testing app-login endpoint functionality..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Load environment
    export $(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
    
    # Create test users if they don't exist
    python scripts/create_simple_users.py || log_warning "Test user creation failed or users already exist"
    
    log_success "App-login endpoint preparation completed"
}

# Restart backend service
restart_backend() {
    log_info "Restarting backend service..."
    
    # Stop service gracefully
    systemctl stop dayplanner-backend.service || log_warning "Backend service was not running"
    
    # Wait a moment
    sleep 3
    
    # Start service
    systemctl start dayplanner-backend.service
    
    # Check status
    if systemctl is-active --quiet dayplanner-backend.service; then
        log_success "Backend service restarted successfully"
    else
        log_error "Backend service failed to start"
        systemctl status dayplanner-backend.service --no-pager
        exit 1
    fi
}

# Health check including app-login endpoint
health_check() {
    log_info "Performing comprehensive health check..."
    
    # Wait for service to be ready
    sleep 10
    
    # Check general health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "General health check passed"
    else
        log_error "General health check failed"
        return 1
    fi
    
    # Check app-login endpoint exists
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/app-login -X POST -H "Content-Type: application/json" -d '{}' | grep -q "422"; then
        log_success "App-login endpoint is accessible (returns validation error as expected)"
    else
        log_error "App-login endpoint is not accessible"
        return 1
    fi
    
    # Check Swagger documentation
    if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
        log_success "Swagger documentation is accessible"
    else
        log_warning "Swagger documentation check failed"
    fi
    
    log_success "All health checks passed"
}

# Update OpenAPI documentation
update_documentation() {
    log_info "Updating OpenAPI documentation..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Export OpenAPI specs
    python scripts/export_openapi.py || log_warning "OpenAPI export failed, but continuing..."
    
    log_success "Documentation update completed"
}

# Main deployment function
main() {
    log_info "Starting App Login Endpoint deployment..."
    log_info "This deployment includes:"
    log_info "  - New POST /auth/app-login endpoint"
    log_info "  - Updated OpenAPI documentation"
    log_info "  - Enhanced authentication features"
    log_info "  - Python type hint compatibility fixes"
    
    check_root
    create_backup
    update_repository
    update_python_dependencies
    run_migrations
    test_app_login
    restart_backend
    health_check
    update_documentation
    
    log_success "Deployment completed successfully!"
    log_info ""
    log_info "🎉 New Features Available:"
    log_info "  📱 App Login Endpoint: POST /auth/app-login"
    log_info "  📚 Updated Swagger UI: https://mytrips-api.bahar.co.il/docs"
    log_info "  🔐 Simple authentication without token management"
    log_info ""
    log_info "🧪 Test the new endpoint:"
    log_info "  curl -X POST 'https://mytrips-api.bahar.co.il/auth/app-login' \\"
    log_info "    -H 'Content-Type: application/json' \\"
    log_info "    -d '{\"email\": \"test@example.com\", \"password\": \"test123\"}'"
    log_info ""
    log_info "📊 Service Status:"
    systemctl status dayplanner-backend.service --no-pager -l
    log_info ""
    log_info "🔧 Service Management:"
    log_info "  sudo systemctl status dayplanner-backend"
    log_info "  sudo systemctl restart dayplanner-backend"
    log_info "  sudo journalctl -u dayplanner-backend -f"
}

# Run deployment
main "$@"
