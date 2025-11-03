#!/bin/bash

# DayPlanner Quick Start Production Deployment
# One-command deployment script for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Banner
echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DayPlanner Deployment                    ║"
echo "║              Production Setup Without Docker                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

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
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Welcome message
log_info "Welcome to DayPlanner production deployment!"
echo
log_warning "This script will:"
echo "  • Install system dependencies"
echo "  • Set up the application in /opt/dayplanner"
echo "  • Configure systemd services"
echo "  • Set up Nginx reverse proxy"
echo "  • Run database migrations"
echo "  • Start all services"
echo

# Confirm deployment
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Deployment cancelled"
    exit 0
fi

# Check if this is a fresh installation or update
if [ -d "/opt/dayplanner" ]; then
    log_warning "Existing installation detected at /opt/dayplanner"
    read -p "Do you want to update the existing installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Running update process..."
        /opt/dayplanner/deployment/scripts/update.sh
        exit 0
    else
        log_error "Please backup and remove /opt/dayplanner before fresh installation"
        exit 1
    fi
fi

# Environment configuration
log_info "Setting up environment configuration..."
echo

# Check if we're in the repository directory
if [ ! -f "deployment/production.env" ]; then
    log_error "This script must be run from the DayPlanner repository root"
    log_info "Please run: git clone https://github.com/AdarBahar/MyTrip.git && cd MyTrip"
    exit 1
fi

# Deploy clean application to /opt/dayplanner
log_info "Deploying clean application to /opt/dayplanner..."
if [ -f ".deployignore" ]; then
    rsync -av --exclude-from=.deployignore . /opt/dayplanner/
    log_success "Clean deployment completed using .deployignore"
else
    log_warning ".deployignore not found, using manual exclusions"
    rsync -av \
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
          . /opt/dayplanner/
    log_success "Clean deployment completed using manual exclusions"
fi
cd /opt/dayplanner

# Environment setup
if [ ! -f ".env.production" ]; then
    log_info "Creating production environment file..."
    cp deployment/production.env .env.production

    log_warning "IMPORTANT: You need to configure the environment file!"
    log_info "Please edit /opt/dayplanner/.env.production with your settings:"
    echo "  • Database connection details"
    echo "  • API keys (GraphHopper, MapTiler)"
    echo "  • Domain name and URLs"
    echo "  • Security settings"
    echo

    read -p "Do you want to edit the environment file now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        nano .env.production
    else
        log_warning "Remember to edit /opt/dayplanner/.env.production before starting services!"
    fi
fi

# Run the main deployment script
log_info "Running main deployment script..."
deployment/scripts/deploy.sh

# Optional GraphHopper setup
echo
log_info "GraphHopper Routing Setup"
echo "You can use either:"
echo "  1. GraphHopper Cloud API (requires API key)"
echo "  2. Self-hosted GraphHopper (requires more setup but free)"
echo

read -p "Do you want to set up self-hosted GraphHopper? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    deployment/scripts/setup-graphhopper.sh
fi

# Final health check
log_info "Performing final health check..."
sleep 10

# Check services
if systemctl is-active --quiet dayplanner-backend.service; then
    log_success "Backend service is running"
else
    log_error "Backend service is not running"
fi

if systemctl is-active --quiet dayplanner-frontend.service; then
    log_success "Frontend service is running"
else
    log_error "Frontend service is not running"
fi

# Check application health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log_success "Backend health check passed"
else
    log_warning "Backend health check failed"
fi

if curl -f http://localhost:3500 > /dev/null 2>&1; then
    log_success "Frontend health check passed"
else
    log_warning "Frontend health check failed"
fi

# Success message
echo
log_success "🎉 DayPlanner deployment completed!"
echo
echo -e "${BOLD}Access your application:${NC}"
echo "  🌐 Frontend: http://localhost (via Nginx)"
echo "  🔧 Backend API: http://localhost/api"
echo "  📚 API Docs: http://localhost/docs"
echo

echo -e "${BOLD}Service management:${NC}"
echo "  sudo systemctl status dayplanner-backend"
echo "  sudo systemctl status dayplanner-frontend"
echo "  sudo systemctl restart dayplanner-backend"
echo "  sudo systemctl restart dayplanner-frontend"
echo

echo -e "${BOLD}Logs:${NC}"
echo "  sudo journalctl -u dayplanner-backend -f"
echo "  sudo journalctl -u dayplanner-frontend -f"
echo "  sudo tail -f /var/log/dayplanner/*.log"
echo

echo -e "${BOLD}Next steps:${NC}"
echo "  1. Configure SSL/HTTPS (recommended for production)"
echo "  2. Set up monitoring and backups"
echo "  3. Configure firewall rules"
echo "  4. Test all application functionality"
echo

log_info "For detailed documentation, see: deployment/README.md"
log_info "For deployment checklist, see: deployment/DEPLOYMENT_CHECKLIST.md"

echo
log_success "Happy trip planning! 🚗💨"
