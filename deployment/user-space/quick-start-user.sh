#!/bin/bash

# DayPlanner User-Space Quick Start
# One-command deployment without root access

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
echo "║                DayPlanner User-Space Deployment             ║"
echo "║                   No Root Access Required                   ║"
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

# Check if running as regular user
if [[ $EUID -eq 0 ]]; then
    log_error "This script should NOT be run as root"
    log_info "Run as regular user: ./deployment/user-space/quick-start-user.sh"
    exit 1
fi

# Welcome message
log_info "Welcome to DayPlanner user-space deployment!"
echo
log_warning "This script will:"
echo "  • Install Node.js via NVM (user-level)"
echo "  • Set up Python virtual environment"
echo "  • Install PM2 process manager"
echo "  • Deploy the application to ~/dayplanner"
echo "  • Start services on ports 3500 (frontend) and 8000 (backend)"
echo

# Check if this is a fresh installation or update
if [ -d "$HOME/dayplanner" ]; then
    log_warning "Existing installation detected at ~/dayplanner"
    read -p "Do you want to update the existing installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Running update process..."
        ~/dayplanner/deployment/user-space/update-user.sh
        exit 0
    else
        log_error "Please backup and remove ~/dayplanner before fresh installation"
        exit 1
    fi
fi

# Confirm deployment
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Deployment cancelled"
    exit 0
fi

# Check if we're in the repository directory
if [ ! -f "deployment/user-space/user-production.env" ]; then
    log_info "Cloning DayPlanner repository..."
    git clone https://github.com/AdarBahar/MyTrip.git ~/dayplanner
    cd ~/dayplanner
else
    log_info "Using current directory as source..."
    # Copy current directory to ~/dayplanner
    cp -r . ~/dayplanner/
    cd ~/dayplanner
fi

# Environment setup
if [ ! -f ".env.production" ]; then
    log_info "Creating production environment file..."
    cp deployment/user-space/user-production.env .env.production
    
    log_warning "IMPORTANT: You need to configure the environment file!"
    log_info "Please edit ~/dayplanner/.env.production with your settings:"
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
        log_warning "Remember to edit ~/dayplanner/.env.production before starting services!"
    fi
fi

# Run the main deployment script
log_info "Running user-space deployment script..."
./deployment/user-space/deploy-user.sh

# Final status check
log_info "Performing final status check..."
sleep 5

# Source nvm for PM2 commands
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Check PM2 status
if pm2 list | grep -q "dayplanner"; then
    log_success "PM2 services are running"
    pm2 status
else
    log_warning "PM2 services not detected"
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

# Get server IP for access URLs
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

# Success message
echo
log_success "🎉 DayPlanner user-space deployment completed!"
echo
echo -e "${BOLD}Access your application:${NC}"
echo "  🌐 Frontend: http://$SERVER_IP:3500"
echo "  🔧 Backend API: http://$SERVER_IP:8000"
echo "  📚 API Docs: http://$SERVER_IP:8000/docs"
echo

echo -e "${BOLD}Management commands:${NC}"
echo "  ~/dayplanner/start.sh     - Start services"
echo "  ~/dayplanner/stop.sh      - Stop services"
echo "  ~/dayplanner/restart.sh   - Restart services"
echo "  ~/dayplanner/status.sh    - Check status"
echo

echo -e "${BOLD}PM2 commands:${NC}"
echo "  pm2 status                - Service status"
echo "  pm2 logs                  - View logs"
echo "  pm2 restart all           - Restart all services"
echo "  pm2 stop all              - Stop all services"
echo

echo -e "${BOLD}Logs and monitoring:${NC}"
echo "  pm2 logs dayplanner-backend"
echo "  pm2 logs dayplanner-frontend"
echo "  tail -f ~/dayplanner/logs/*.log"
echo

echo -e "${BOLD}Important files:${NC}"
echo "  📁 App directory: ~/dayplanner"
echo "  ⚙️  Environment: ~/dayplanner/.env.production"
echo "  📊 PM2 config: ~/dayplanner/ecosystem.config.js"
echo "  📝 Logs: ~/dayplanner/logs/"
echo "  💾 Backups: ~/dayplanner-backups/"
echo

echo -e "${BOLD}Next steps:${NC}"
echo "  1. Test application functionality"
echo "  2. Configure your domain/DNS (if applicable)"
echo "  3. Set up SSL/HTTPS (if available)"
echo "  4. Configure firewall to allow ports 3500 and 8000"
echo "  5. Set up monitoring and backups"
echo

echo -e "${BOLD}Troubleshooting:${NC}"
echo "  📖 Documentation: ~/dayplanner/deployment/user-space/README.md"
echo "  🔧 Update app: ~/dayplanner/deployment/user-space/update-user.sh"
echo "  🗄️  Migrate DB: ~/dayplanner/deployment/user-space/migrate-user.sh"
echo

log_info "For detailed documentation, see: ~/dayplanner/deployment/user-space/README.md"

echo
log_success "Happy trip planning! 🚗💨"

# Show current PM2 status
echo
echo -e "${BOLD}Current Service Status:${NC}"
pm2 status 2>/dev/null || log_warning "PM2 not available in current shell. Run: source ~/.bashrc"
