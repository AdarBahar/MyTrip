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
    cd "$APP_DIR"

    # Always fetch and show pending changes if repo exists
    if [ -d .git ]; then
        log_info "Fetching latest changes..."
        git fetch origin || true
        log_info "Changes to be applied:"
        git log --oneline HEAD..origin/main || true

        # Ask for confirmation in interactive mode
        if [ -t 0 ]; then
            read -p "Do you want to proceed with the update? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_warning "Update cancelled by user"
                exit 0
            fi
        fi
    fi

    if [ "$THIN_DEPLOY" = "1" ]; then
        log_info "Updating code using THIN deployment (rsync + .deployignore)..."

        # Determine origin URL
        ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
        if [ -z "$ORIGIN_URL" ]; then
            log_error "Unable to determine git origin URL in $APP_DIR"
            exit 1
        fi

        # Prepare temp dir
        tmpdir="/tmp/dayplanner-release-$(date +%Y%m%d_%H%M%S)"
        log_info "Cloning repository into $tmpdir ..."
        git clone --depth 1 --branch main "$ORIGIN_URL" "$tmpdir"

        # Rsync only necessary files into APP_DIR, preserving venv/node_modules and excluding dev files
        log_info "Syncing files to $APP_DIR with exclusions (.deployignore)..."
        # Optionally exclude the frontend entirely in backend-only mode
        rsync_exclude_frontend=""
        if [ "$BACKEND_ONLY" = "1" ]; then
            rsync_exclude_frontend="--exclude=frontend/"
        fi
        rsync -a --delete \
            --exclude-from="$tmpdir/.deployignore" \
            --exclude='.env.production' \
            --exclude='backend/venv/' \
            --exclude='frontend/node_modules/' \
            --exclude='.git/' \
            $rsync_exclude_frontend \
            "$tmpdir/" "$APP_DIR/"
        # If backend-only, ensure any existing frontend is removed
        if [ "$BACKEND_ONLY" = "1" ]; then
            rm -rf "$APP_DIR/frontend"
        fi

        # Preserve ownership
        chown -R www-data:www-data "$APP_DIR"

        # Cleanup
        rm -rf "$tmpdir"

        log_success "Thin code update completed"
    else
        log_info "Updating code from Git repository (git pull)..."
        git pull origin main
        log_success "Code updated successfully"
    fi
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

    if command -v pnpm >/dev/null 2>&1; then
        # Preferred: pnpm
        log_info "Using pnpm for frontend build"
        sudo -u www-data pnpm install
        sudo -u www-data pnpm build
        if [ "$THIN_DEPLOY" = "1" ]; then
            log_info "Pruning development dependencies for thin deployment (pnpm)..."
            sudo -u www-data pnpm prune --prod || true
        fi
    elif command -v npm >/dev/null 2>&1; then
        # Fallback: npm
        log_warning "pnpm not found, falling back to npm"
        # Use ci if lockfile exists, otherwise install
        if [ -f package-lock.json ]; then
            sudo -u www-data npm ci || sudo -u www-data npm install
        else
            sudo -u www-data npm install
        fi
        sudo -u www-data npm run build
        if [ "$THIN_DEPLOY" = "1" ]; then
            log_info "Pruning development dependencies for thin deployment (npm)..."
            sudo -u www-data npm prune --production || true
        fi
    else
        log_error "Neither pnpm nor npm found. Please install one of them (e.g., 'sudo npm install -g pnpm' or 'sudo apt-get install -y npm')."
        exit 1
    fi

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

    # Start frontend unless in backend-only mode
    if [ "$BACKEND_ONLY" != "1" ]; then
        systemctl start dayplanner-frontend.service
    else
        log_info "Skipping frontend service start (backend-only mode)"
    fi

    # Check status
    systemctl status dayplanner-backend.service --no-pager
    if [ "$BACKEND_ONLY" != "1" ]; then
        systemctl status dayplanner-frontend.service --no-pager
    fi

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

    # Check frontend (skip in backend-only mode)
    if [ "$BACKEND_ONLY" != "1" ]; then
        if curl -f http://localhost:3500 > /dev/null 2>&1; then
            log_success "Frontend health check passed"
        else
            log_error "Frontend health check failed"
            return 1
        fi
    else
        log_info "Skipping frontend health check (backend-only mode)"
    fi

    log_success "All health checks passed"
}

# Remove non-runtime files to keep production deployment thin
thin_cleanup() {
    log_info "Applying thin deployment cleanup..."
    cd "$APP_DIR"

    # Remove documentation and markdown files (keep deployment scripts)
    find "$APP_DIR" -type f -name "*.md" \
        -not -path "$APP_DIR/deployment/*" \
        -not -path "$APP_DIR/frontend/node_modules/*" \
        -not -path "$APP_DIR/backend/venv/*" \
        -delete 2>/dev/null || true

    # Remove test and docs directories
    rm -rf "$APP_DIR/backend/tests" "$APP_DIR/backend/docs" 2>/dev/null || true
    rm -rf "$APP_DIR/frontend/tests" "$APP_DIR/frontend/docs" 2>/dev/null || true

    # Remove debug/demo example pages not needed in production
    rm -rf "$APP_DIR/frontend/app/debug"* 2>/dev/null || true
    rm -rf "$APP_DIR/frontend/app/test" "$APP_DIR/frontend/app/test-page" 2>/dev/null || true
    rm -rf "$APP_DIR/frontend/app/demo" "$APP_DIR/frontend/app/debug-demo" "$APP_DIR/frontend/app/migration-demo" 2>/dev/null || true
    rm -rf "$APP_DIR/frontend/components/debug" "$APP_DIR/frontend/components/test" 2>/dev/null || true

    # Remove development-only deployment content
    rm -rf "$APP_DIR/deployment/production" "$APP_DIR/deployment/user-space" 2>/dev/null || true

    # Python caches
    find "$APP_DIR/backend" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$APP_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true

    # If backend-only deployment, remove frontend entirely
    if [ "$BACKEND_ONLY" = "1" ]; then
        rm -rf "$APP_DIR/frontend" 2>/dev/null || true
    fi

    log_success "Thin cleanup complete"
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
        if [ "$BACKEND_ONLY" != "1" ]; then
            systemctl start dayplanner-frontend.service
        else
            log_info "Skipping frontend service start (backend-only mode)"
        fi

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
    if [ "$BACKEND_ONLY" != "1" ]; then
        update_frontend
    else
        log_info "Skipping frontend update (backend-only mode)"
    fi
    run_migrations
    # Optional thin cleanup before starting services
    if [ "$THIN_DEPLOY" = "1" ]; then
        thin_cleanup
    fi

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
    --thin)
        THIN_DEPLOY=1
        main
        ;;
    --backend-only)
        BACKEND_ONLY=1
        main
        ;;
    --thin-backend)
        THIN_DEPLOY=1
        BACKEND_ONLY=1
        main
        ;;
    --help)
        echo "Usage: $0 [--thin] [--backend-only] [--thin-backend] [--rollback] [--help]"
        echo "  --thin           Thin-deploy cleanup (remove docs/tests/MD files, prune dev deps)"
        echo "  --backend-only   Update only backend (skip frontend sync/build/start; no frontend health check)"
        echo "  --thin-backend   Thin deploy + backend-only (exclude frontend from rsync; remove frontend dir)"
        echo "  --rollback       Rollback to the previous deployment"
        echo "  --help           Show this help message"
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
