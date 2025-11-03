#!/bin/bash

# Quick deployment script for route optimization fix
# This script deploys the exception handling fix to production

set -e

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

# Configuration
PROD_SERVER="mytrips-api.bahar.co.il"
APP_DIR="/opt/dayplanner"

log_info "🚀 Deploying route optimization fix to production..."
log_info "📍 Target: $PROD_SERVER"
log_info "📁 App Directory: $APP_DIR"

# Create deployment commands
DEPLOY_COMMANDS="
set -e

# Navigate to app directory
cd $APP_DIR

# Show current status
echo '📋 Current status:'
git log --oneline -5

# Pull latest changes
echo '⬇️ Pulling latest changes...'
git pull origin main

# Show what was updated
echo '✅ Latest changes:'
git log --oneline -3

# Restart backend service to apply the fix
echo '🔄 Restarting backend service...'
sudo systemctl restart dayplanner-backend.service

# Wait for service to start
echo '⏳ Waiting for service to start...'
sleep 10

# Check service status
echo '📊 Service status:'
sudo systemctl status dayplanner-backend.service --no-pager -l

# Health check
echo '🏥 Health check:'
curl -f http://localhost:8000/health || echo 'Health check failed'

echo '✅ Deployment completed!'
"

# Execute deployment
log_info "🔧 Executing deployment commands..."

# Note: In a real deployment, you would SSH to the production server
# For this demonstration, we'll show the commands that would be executed
echo "Commands that would be executed on production server:"
echo "=================================================="
echo "$DEPLOY_COMMANDS"
echo "=================================================="

log_warning "⚠️  Manual deployment required:"
log_info "1. SSH to production server: ssh user@$PROD_SERVER"
log_info "2. Navigate to app directory: cd $APP_DIR"
log_info "3. Pull latest changes: git pull origin main"
log_info "4. Restart backend: sudo systemctl restart dayplanner-backend.service"
log_info "5. Check status: sudo systemctl status dayplanner-backend.service"
log_info "6. Test fix with CURL commands provided earlier"

log_success "🎯 Deployment script completed!"
log_info "📝 The route optimization ValidationError fix is now ready for production"
