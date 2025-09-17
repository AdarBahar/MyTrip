#!/bin/bash

# DayPlanner User-Space Deployment Script
# Deploy without root access using user-level tools

set -e

# Configuration
APP_DIR="$HOME/dayplanner"
BACKUP_DIR="$HOME/dayplanner-backups"
LOG_DIR="$HOME/dayplanner/logs"
NODE_VERSION="18.17.0"

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

# Check if we're not running as root
check_user() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should NOT be run as root"
        log_info "Run as regular user: ./deployment/user-space/deploy-user.sh"
        exit 1
    fi
    log_success "Running as user: $(whoami)"
}

# Create necessary directories
create_directories() {
    log_info "Creating user directories..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$HOME/.local/bin"
    
    log_success "Directories created"
}

# Install Node.js via NVM (if not already installed)
install_nodejs() {
    log_info "Setting up Node.js..."
    
    # Check if nvm is installed
    if [ ! -f "$HOME/.nvm/nvm.sh" ]; then
        log_info "Installing NVM..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        
        # Source nvm
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    else
        # Source nvm
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        log_success "NVM already installed"
    fi
    
    # Install and use Node.js
    nvm install $NODE_VERSION
    nvm use $NODE_VERSION
    nvm alias default $NODE_VERSION
    
    # Install pnpm and PM2 globally
    npm install -g pnpm pm2
    
    log_success "Node.js $NODE_VERSION installed with pnpm and PM2"
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
    
    log_success "Python environment setup complete"
}

# Build frontend
build_frontend() {
    log_info "Building frontend for production..."
    
    cd "$APP_DIR/frontend"
    
    # Source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    # Install dependencies and build
    pnpm install
    pnpm build
    
    log_success "Frontend build complete"
}

# Create PM2 ecosystem file
create_pm2_config() {
    log_info "Creating PM2 configuration..."
    
    cat > "$APP_DIR/ecosystem.config.js" << EOF
module.exports = {
  apps: [
    {
      name: 'dayplanner-backend',
      cwd: '$APP_DIR/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000 --workers 2',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '$APP_DIR/backend'
      },
      env_file: '$APP_DIR/.env.production',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '$LOG_DIR/backend-error.log',
      out_file: '$LOG_DIR/backend-out.log',
      log_file: '$LOG_DIR/backend-combined.log',
      time: true
    },
    {
      name: 'dayplanner-frontend',
      cwd: '$APP_DIR/frontend',
      script: 'server.js',
      env: {
        NODE_ENV: 'production',
        PORT: 3500
      },
      env_file: '$APP_DIR/.env.production',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      error_file: '$LOG_DIR/frontend-error.log',
      out_file: '$LOG_DIR/frontend-out.log',
      log_file: '$LOG_DIR/frontend-combined.log',
      time: true
    }
  ]
};
EOF
    
    log_success "PM2 configuration created"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$APP_DIR/backend"
    source venv/bin/activate
    
    # Load environment
    export \$(cat "$APP_DIR/.env.production" | grep -v '^#' | xargs)
    
    # Run migrations
    alembic upgrade head
    
    log_success "Database migrations complete"
}

# Start services with PM2
start_services() {
    log_info "Starting services with PM2..."
    
    # Source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    cd "$APP_DIR"
    
    # Start services
    pm2 start ecosystem.config.js
    
    # Save PM2 configuration
    pm2 save
    
    # Setup PM2 startup (user-level)
    pm2 startup
    
    log_success "Services started with PM2"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Wait for services to start
    sleep 10
    
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

# Create management scripts
create_management_scripts() {
    log_info "Creating management scripts..."
    
    # Create start script
    cat > "$APP_DIR/start.sh" << 'EOF'
#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
cd "$HOME/dayplanner"
pm2 start ecosystem.config.js
EOF
    
    # Create stop script
    cat > "$APP_DIR/stop.sh" << 'EOF'
#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
pm2 stop all
EOF
    
    # Create restart script
    cat > "$APP_DIR/restart.sh" << 'EOF'
#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
cd "$HOME/dayplanner"
pm2 restart all
EOF
    
    # Create status script
    cat > "$APP_DIR/status.sh" << 'EOF'
#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
pm2 status
pm2 logs --lines 20
EOF
    
    # Make scripts executable
    chmod +x "$APP_DIR"/*.sh
    
    log_success "Management scripts created"
}

# Main deployment function
main() {
    log_info "Starting DayPlanner user-space deployment..."
    
    check_user
    create_directories
    install_nodejs
    setup_python_env
    build_frontend
    create_pm2_config
    run_migrations
    start_services
    health_check
    create_management_scripts
    
    log_success "Deployment completed successfully!"
    log_info ""
    log_info "🌐 Application URLs:"
    log_info "  Frontend: http://$(hostname -I | awk '{print $1}'):3500"
    log_info "  Backend:  http://$(hostname -I | awk '{print $1}'):8000"
    log_info "  API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
    log_info ""
    log_info "📋 Management commands:"
    log_info "  Start:    $APP_DIR/start.sh"
    log_info "  Stop:     $APP_DIR/stop.sh"
    log_info "  Restart:  $APP_DIR/restart.sh"
    log_info "  Status:   $APP_DIR/status.sh"
    log_info ""
    log_info "📊 PM2 commands:"
    log_info "  pm2 status"
    log_info "  pm2 logs"
    log_info "  pm2 restart all"
    log_info "  pm2 stop all"
    log_info ""
    log_info "📁 Important paths:"
    log_info "  App:      $APP_DIR"
    log_info "  Logs:     $LOG_DIR"
    log_info "  Backups:  $BACKUP_DIR"
}

# Run deployment
main "$@"
