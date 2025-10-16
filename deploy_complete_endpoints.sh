#!/bin/bash

# Complete Endpoints & Short Format - Production Deployment Script
# This script deploys all files needed for the complete endpoints and short format features
# Commit: 4ac634d (includes all fixes)

set -e  # Exit on any error

# Configuration
SERVER="65.109.171.65"
USER="root"
SSH_KEY="~/.ssh/hetzner-mytrips-api"
BACKEND_PATH="/opt/dayplanner/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if SSH key exists
    if [ ! -f ~/.ssh/hetzner-mytrips-api ]; then
        log_error "SSH key not found at ~/.ssh/hetzner-mytrips-api"
        exit 1
    fi
    
    # Check if required files exist
    local files=(
        "backend/app/schemas/trip_complete.py"
        "backend/app/schemas/trip_short.py"
        "backend/app/api/days/router.py"
        "backend/app/api/trips/router.py"
        "backend/app/schemas/day.py"
    )
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "All prerequisites met"
}

# Backup current files on server
backup_current_files() {
    log_info "Creating backup of current files on server..."
    
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        cd $BACKEND_PATH
        mkdir -p backups/$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR=backups/$(date +%Y%m%d_%H%M%S)
        
        # Backup existing files
        [ -f app/api/days/router.py ] && cp app/api/days/router.py \$BACKUP_DIR/
        [ -f app/api/trips/router.py ] && cp app/api/trips/router.py \$BACKUP_DIR/
        [ -f app/schemas/day.py ] && cp app/schemas/day.py \$BACKUP_DIR/
        [ -f app/schemas/trip_complete.py ] && cp app/schemas/trip_complete.py \$BACKUP_DIR/
        [ -f app/schemas/trip_short.py ] && cp app/schemas/trip_short.py \$BACKUP_DIR/
        
        echo 'Backup created in:' \$BACKUP_DIR
    "
    
    log_success "Backup completed"
}

# Upload files to server
upload_files() {
    log_info "Uploading files to production server..."
    
    # Upload new schema files
    log_info "Uploading schema files..."
    scp -i "$SSH_KEY" \
        backend/app/schemas/trip_complete.py \
        backend/app/schemas/trip_short.py \
        "$USER@$SERVER:$BACKEND_PATH/app/schemas/"
    
    # Upload modified schema file
    scp -i "$SSH_KEY" \
        backend/app/schemas/day.py \
        "$USER@$SERVER:$BACKEND_PATH/app/schemas/"
    
    # Upload router files
    log_info "Uploading router files..."
    scp -i "$SSH_KEY" \
        backend/app/api/days/router.py \
        "$USER@$SERVER:$BACKEND_PATH/app/api/days/"
    
    scp -i "$SSH_KEY" \
        backend/app/api/trips/router.py \
        "$USER@$SERVER:$BACKEND_PATH/app/api/trips/"
    
    log_success "All files uploaded successfully"
}

# Test Python imports on server
test_imports() {
    log_info "Testing Python imports on server..."
    
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        cd $BACKEND_PATH
        source venv/bin/activate
        
        # Test individual imports
        python -c 'from app.schemas.trip_complete import TripCompleteResponse; print(\"✅ trip_complete import OK\")'
        python -c 'from app.schemas.trip_short import TripShortResponse; print(\"✅ trip_short import OK\")'
        python -c 'from app.api.days.router import router; print(\"✅ days router import OK\")'
        python -c 'from app.api.trips.router import router; print(\"✅ trips router import OK\")'
        
        # Test main app import
        python -c 'from app.main import app; print(\"✅ Main app import OK\")'
    "
    
    log_success "All imports successful"
}

# Restart service
restart_service() {
    log_info "Restarting dayplanner-backend service..."
    
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        systemctl restart dayplanner-backend
        sleep 3
        systemctl is-active dayplanner-backend
    "
    
    log_success "Service restarted successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    log_info "Checking service status..."
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        systemctl status dayplanner-backend --no-pager -l | head -20
    "
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        curl -s http://localhost:8000/health | head -5
    "
    
    # Test Swagger docs
    log_info "Testing Swagger documentation..."
    ssh -i "$SSH_KEY" "$USER@$SERVER" "
        curl -s http://localhost:8000/openapi.json | grep -q 'complete' && echo '✅ Complete endpoints in Swagger' || echo '❌ Complete endpoints missing'
        curl -s http://localhost:8000/openapi.json | grep -q 'short' && echo '✅ Short format in Swagger' || echo '❌ Short format missing'
    "
    
    log_success "Deployment verification completed"
}

# Main deployment function
main() {
    echo "🚀 Complete Endpoints & Short Format Deployment"
    echo "================================================"
    echo "Commit: 4ac634d (includes all fixes)"
    echo "Target: $USER@$SERVER:$BACKEND_PATH"
    echo ""
    
    # Confirm deployment
    read -p "Deploy to production? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment steps
    check_prerequisites
    backup_current_files
    upload_files
    test_imports
    restart_service
    verify_deployment
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Test the new endpoints:"
    echo "   curl 'https://mytrips-api.bahar.co.il/trips?format=short&size=2'"
    echo "2. Check Swagger docs at: https://mytrips-api.bahar.co.il/docs"
    echo "3. Monitor service logs if needed:"
    echo "   ssh -i $SSH_KEY $USER@$SERVER 'journalctl -u dayplanner-backend -f'"
    echo ""
    log_success "All features are now live in production! 🚀"
}

# Run main function
main "$@"
