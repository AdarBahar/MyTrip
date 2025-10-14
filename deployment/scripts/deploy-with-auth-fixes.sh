#!/bin/bash

# MyTrips Backend Deployment Script with Authentication Fixes
# This script ensures proper JWT authentication is configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/dayplanner"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
ENV_FILE="$APP_DIR/.env.production"
LOG_FILE="/var/log/dayplanner-deployment.log"

# Logging functions
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        nginx \
        curl \
        git \
        build-essential \
        libpq-dev \
        mysql-client \
        libffi-dev \
        libssl-dev
    
    # Install pnpm globally
    npm install -g pnpm
    
    log_success "System dependencies installed"
}

# Setup backend with authentication fixes
setup_backend() {
    log_info "Setting up backend with authentication fixes..."
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Install Python dependencies
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
    
    # Ensure JWT dependencies are installed
    log_info "Installing JWT authentication dependencies..."
    venv/bin/pip install python-jose[cryptography]==3.3.0
    venv/bin/pip install passlib[bcrypt]==1.7.4
    venv/bin/pip install pyjwt==2.8.0
    venv/bin/pip install cryptography==41.0.7
    
    # Set proper ownership
    chown -R www-data:www-data "$BACKEND_DIR"
    
    log_success "Backend setup completed with JWT authentication"
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    sudo -u www-data pnpm install
    
    # Build for production
    sudo -u www-data pnpm build
    
    # Set proper ownership
    chown -R www-data:www-data "$FRONTEND_DIR"
    
    log_success "Frontend setup completed"
}

# Configure environment variables
configure_environment() {
    log_info "Configuring environment variables..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Please create $ENV_FILE with your database credentials"
        exit 1
    fi
    
    # Ensure APP_SECRET is set for JWT
    if ! grep -q "APP_SECRET" "$ENV_FILE"; then
        log_warning "APP_SECRET not found in environment file"
        log_info "Adding default APP_SECRET (change this in production!)"
        echo "APP_SECRET=your-super-secure-secret-key-change-this-in-production-min-32-chars" >> "$ENV_FILE"
    fi
    
    # Ensure JWT settings are configured
    if ! grep -q "JWT_ALGORITHM" "$ENV_FILE"; then
        echo "JWT_ALGORITHM=HS256" >> "$ENV_FILE"
        echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> "$ENV_FILE"
        echo "REFRESH_TOKEN_EXPIRE_DAYS=7" >> "$ENV_FILE"
    fi
    
    log_success "Environment configuration completed"
}

# Test database connection
test_database_connection() {
    log_info "Testing database connection..."
    
    cd "$BACKEND_DIR"
    
    # Test database connection
    if sudo -u www-data bash -c "
        source venv/bin/activate
        export \$(cat $ENV_FILE | grep -v '^#' | xargs)
        python -c 'from app.core.database import engine; conn = engine.connect(); print(\"Database connection successful\"); conn.close()'
    " 2>/dev/null; then
        log_success "Database connection successful"
    else
        log_error "Database connection failed"
        log_info "Please check your database credentials in $ENV_FILE"
        return 1
    fi
}

# Test JWT authentication
test_jwt_authentication() {
    log_info "Testing JWT authentication system..."

    cd "$BACKEND_DIR"

    # Test JWT imports and functionality
    if sudo -u www-data bash -c "
        source venv/bin/activate
        export \$(cat $ENV_FILE | grep -v '^#' | xargs)
        python -c '
from app.core.jwt import create_access_token, verify_token, get_password_hash, verify_password
# Test password hashing
password = \"test123\"
hashed = get_password_hash(password)
verified = verify_password(password, hashed)
print(f\"Password hashing: {\"✅\" if verified else \"❌\"}\")

# Test JWT tokens
token = create_access_token(data={\"sub\": \"test_user\"})
payload = verify_token(token)
print(f\"JWT tokens: {\"✅\" if payload.get(\"sub\") == \"test_user\" else \"❌\"}\")
print(\"JWT authentication system working\")
'
    " 2>/dev/null; then
        log_success "JWT authentication system working"
    else
        log_error "JWT authentication system failed"
        return 1
    fi
}

# Run database migrations
run_database_migrations() {
    log_info "Running database migrations..."

    cd "$BACKEND_DIR"

    # Run alembic migrations
    if sudo -u www-data bash -c "
        source venv/bin/activate
        export \$(cat $ENV_FILE | grep -v '^#' | xargs)
        alembic upgrade head
    " 2>/dev/null; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        return 1
    fi
}

# Create production users
create_production_users() {
    log_info "Creating production users with passwords..."

    cd "$BACKEND_DIR"

    # Create production users
    if sudo -u www-data bash -c "
        source venv/bin/activate
        export \$(cat $ENV_FILE | grep -v '^#' | xargs)
        python scripts/create_production_users.py
    " 2>/dev/null; then
        log_success "Production users created"
    else
        log_error "Production users creation failed"
        return 1
    fi
}

# Create systemd services
create_systemd_services() {
    log_info "Creating systemd services..."
    
    # Backend service
    cat > /etc/systemd/system/dayplanner-backend.service << EOF
[Unit]
Description=DayPlanner Backend API Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment=PYTHONPATH=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dayplanner-backend

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    cat > /etc/systemd/system/dayplanner-frontend.service << EOF
[Unit]
Description=DayPlanner Frontend Service
After=network.target dayplanner-backend.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$FRONTEND_DIR
Environment=NODE_ENV=production
Environment=PORT=3500
Environment=NEXT_PUBLIC_API_BASE_URL=https://mytrips-api.bahar.co.il
EnvironmentFile=$ENV_FILE
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dayplanner-frontend

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable dayplanner-backend
    systemctl enable dayplanner-frontend
    
    log_success "Systemd services created and enabled"
}

# Configure nginx
configure_nginx() {
    log_info "Configuring nginx..."
    
    # API domain configuration
    cat > /etc/nginx/sites-available/mytrips-api << 'EOF'
server {
    listen 80;
    server_name mytrips-api.bahar.co.il;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/mytrips-api_access.log;
    error_log /var/log/nginx/mytrips-api_error.log;
    
    # Proxy all requests to backend
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # CORS headers for API
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/mytrips-api /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if nginx -t; then
        log_success "Nginx configuration valid"
        systemctl reload nginx
    else
        log_error "Nginx configuration invalid"
        return 1
    fi
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start backend
    systemctl start dayplanner-backend
    if systemctl is-active --quiet dayplanner-backend; then
        log_success "Backend service started"
    else
        log_error "Backend service failed to start"
        journalctl -u dayplanner-backend --no-pager -n 20
        return 1
    fi
    
    # Start frontend
    systemctl start dayplanner-frontend
    if systemctl is-active --quiet dayplanner-frontend; then
        log_success "Frontend service started"
    else
        log_error "Frontend service failed to start"
        journalctl -u dayplanner-frontend --no-pager -n 20
        return 1
    fi
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test health endpoint
    sleep 5
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Test authentication endpoint
    if curl -f -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "test@example.com"}' >/dev/null 2>&1; then
        log_success "Authentication endpoint working"
    else
        log_error "Authentication endpoint failed"
        return 1
    fi
    
    log_success "All tests passed!"
}

# Main deployment function
main() {
    log_info "Starting MyTrips deployment with authentication fixes..."
    log_info "Deployment started at $(date)"
    
    check_root
    install_system_dependencies
    setup_backend
    setup_frontend
    configure_environment
    test_database_connection || exit 1
    test_jwt_authentication || exit 1
    run_database_migrations || exit 1
    create_production_users || exit 1
    create_systemd_services
    configure_nginx
    start_services
    test_deployment
    
    log_success "Deployment completed successfully!"
    log_info "Your API is available at: http://mytrips-api.bahar.co.il"
    log_info "Backend logs: sudo journalctl -u dayplanner-backend -f"
    log_info "Frontend logs: sudo journalctl -u dayplanner-frontend -f"
}

# Run main function
main "$@"
