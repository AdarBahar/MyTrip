#!/bin/bash

# Production Deployment Script for Trips Sorting Feature
# Supports rollback if deployment fails
# Usage: ./deploy-trips-sorting.sh [--rollback] [--dry-run] [--server SERVER]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_ID="trips-sorting-$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="/tmp/mytrips-backup-$DEPLOYMENT_ID"

# Default production server configuration
PROD_SERVER="${PROD_SERVER:-your-server.com}"
PROD_USER="${PROD_USER:-deploy}"
PROD_APP_DIR="${PROD_APP_DIR:-/var/www/mytrip}"
PROD_VENV_DIR="${PROD_VENV_DIR:-/var/www/mytrip/venv}"
PROD_SERVICE_NAME="${PROD_SERVICE_NAME:-mytrips-backend}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=false
ROLLBACK=false
VERBOSE=false

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

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${NC}[VERBOSE]${NC} $1"
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --server)
                PROD_SERVER="$2"
                shift 2
                ;;
            --user)
                PROD_USER="$2"
                shift 2
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Production Deployment Script for Trips Sorting Feature

Usage: $0 [OPTIONS]

OPTIONS:
    --rollback          Rollback the last deployment
    --dry-run           Show what would be done without executing
    --server SERVER     Production server hostname/IP (default: $PROD_SERVER)
    --user USER         SSH user (default: $PROD_USER)
    --verbose, -v       Enable verbose output
    --help, -h          Show this help message

ENVIRONMENT VARIABLES:
    PROD_SERVER         Production server hostname/IP
    PROD_USER           SSH user for deployment
    PROD_APP_DIR        Application directory on server
    PROD_VENV_DIR       Python virtual environment directory
    PROD_SERVICE_NAME   Systemd service name

EXAMPLES:
    # Deploy to production
    $0 --server myserver.com --user deploy

    # Dry run to see what would happen
    $0 --dry-run

    # Rollback last deployment
    $0 --rollback

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if we can SSH to the server
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$PROD_USER@$PROD_SERVER" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        log_error "Cannot SSH to $PROD_USER@$PROD_SERVER"
        log_error "Please ensure SSH key authentication is set up"
        exit 1
    fi

    # Check if required files exist
    local required_files=(
        "$PROJECT_ROOT/backend/app/api/trips/router.py"
        "$PROJECT_ROOT/test_trips_sorting.py"
        "$PROJECT_ROOT/docs/TRIPS_SORTING_FEATURE.md"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done

    log_success "Prerequisites check passed"
}

# Create backup on production server
create_backup() {
    log_info "Creating backup on production server..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create backup at $BACKUP_DIR"
        return 0
    fi

    ssh "$PROD_USER@$PROD_SERVER" "
        set -e
        mkdir -p $BACKUP_DIR

        # Backup current backend files
        if [[ -f $PROD_APP_DIR/backend/app/api/trips/router.py ]]; then
            cp $PROD_APP_DIR/backend/app/api/trips/router.py $BACKUP_DIR/router.py.backup
        fi

        # Backup service status
        systemctl is-active $PROD_SERVICE_NAME > $BACKUP_DIR/service_status.txt || echo 'inactive' > $BACKUP_DIR/service_status.txt

        # Create deployment manifest
        cat > $BACKUP_DIR/deployment_manifest.json << 'EOF'
{
    \"deployment_id\": \"$DEPLOYMENT_ID\",
    \"timestamp\": \"$(date -Iseconds)\",
    \"backup_dir\": \"$BACKUP_DIR\",
    \"files_backed_up\": [
        \"backend/app/api/trips/router.py\"
    ]
}
EOF

        echo 'Backup created successfully'
    "

    log_success "Backup created at $BACKUP_DIR"
}

# Upload files to production
upload_files() {
    log_info "Uploading files to production server..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would upload:"
        log_info "  - backend/app/api/trips/router.py"
        log_info "  - test_trips_sorting.py"
        log_info "  - docs/TRIPS_SORTING_FEATURE.md"
        return 0
    fi

    # Upload the modified router.py
    scp "$PROJECT_ROOT/backend/app/api/trips/router.py" \
        "$PROD_USER@$PROD_SERVER:$PROD_APP_DIR/backend/app/api/trips/router.py"

    # Upload test script
    scp "$PROJECT_ROOT/test_trips_sorting.py" \
        "$PROD_USER@$PROD_SERVER:$PROD_APP_DIR/test_trips_sorting.py"

    # Upload documentation
    ssh "$PROD_USER@$PROD_SERVER" "mkdir -p $PROD_APP_DIR/docs"
    scp "$PROJECT_ROOT/docs/TRIPS_SORTING_FEATURE.md" \
        "$PROD_USER@$PROD_SERVER:$PROD_APP_DIR/docs/TRIPS_SORTING_FEATURE.md"

    log_success "Files uploaded successfully"
}

# Restart services
restart_services() {
    log_info "Restarting services on production server..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would restart service: $PROD_SERVICE_NAME"
        return 0
    fi

    ssh "$PROD_USER@$PROD_SERVER" "
        set -e

        # Restart the backend service
        sudo systemctl restart $PROD_SERVICE_NAME

        # Wait for service to start
        sleep 5

        # Check if service is running
        if systemctl is-active --quiet $PROD_SERVICE_NAME; then
            echo 'Service restarted successfully'
        else
            echo 'Service failed to start'
            exit 1
        fi
    "

    log_success "Services restarted successfully"
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run tests on production server"
        return 0
    fi

    # Run health check
    local health_check=$(ssh "$PROD_USER@$PROD_SERVER" "
        curl -s -f http://localhost:8000/health || echo 'FAILED'
    ")

    if [[ "$health_check" == "FAILED" ]]; then
        log_error "Health check failed"
        return 1
    fi

    # Test the new sorting functionality
    ssh "$PROD_USER@$PROD_SERVER" "
        cd $PROD_APP_DIR

        # Run the sorting test script
        python3 test_trips_sorting.py --api-base http://localhost:8000 || {
            echo 'Sorting tests failed'
            exit 1
        }
    "

    log_success "Deployment tests passed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback from backup"
        return 0
    fi

    # Find the most recent backup
    local latest_backup=$(ssh "$PROD_USER@$PROD_SERVER" "
        ls -1t /tmp/mytrips-backup-* 2>/dev/null | head -1 || echo ''
    ")

    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi

    log_info "Rolling back from: $latest_backup"

    ssh "$PROD_USER@$PROD_SERVER" "
        set -e

        # Restore files
        if [[ -f $latest_backup/router.py.backup ]]; then
            cp $latest_backup/router.py.backup $PROD_APP_DIR/backend/app/api/trips/router.py
        fi

        # Restart service
        sudo systemctl restart $PROD_SERVICE_NAME

        # Wait and check
        sleep 5
        if systemctl is-active --quiet $PROD_SERVICE_NAME; then
            echo 'Rollback completed successfully'
        else
            echo 'Rollback failed - service not running'
            exit 1
        fi
    "

    log_success "Rollback completed successfully"
}

# Main deployment function
deploy() {
    log_info "Starting deployment of trips sorting feature..."
    log_info "Deployment ID: $DEPLOYMENT_ID"
    log_info "Target server: $PROD_USER@$PROD_SERVER"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    check_prerequisites
    create_backup
    upload_files
    restart_services

    if ! test_deployment; then
        log_error "Deployment tests failed - initiating rollback"
        rollback_deployment
        exit 1
    fi

    log_success "Deployment completed successfully!"
    log_info "Backup location: $BACKUP_DIR"
    log_info "To rollback: $0 --rollback"
}

# Main script execution
main() {
    parse_args "$@"

    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment
    else
        deploy
    fi
}

# Run main function with all arguments
main "$@"
