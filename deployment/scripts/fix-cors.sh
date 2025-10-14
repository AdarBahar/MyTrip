#!/bin/bash

# CORS Fix Script for MyTrips API
# This script fixes the duplicate CORS headers issue

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

log_info "🔧 Fixing CORS configuration for MyTrips API..."

# Backup current nginx configuration
NGINX_CONFIG="/etc/nginx/sites-available/mytrips-api"
BACKUP_FILE="/etc/nginx/sites-available/mytrips-api.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$NGINX_CONFIG" ]; then
    log_info "Backing up current nginx configuration..."
    cp "$NGINX_CONFIG" "$BACKUP_FILE"
    log_success "Backup created: $BACKUP_FILE"
fi

# Copy the fixed nginx configuration
FIXED_CONFIG="/opt/dayplanner/deployment/nginx/mytrips-api-dev-friendly.conf"

if [ -f "$FIXED_CONFIG" ]; then
    log_info "Installing fixed nginx configuration..."
    cp "$FIXED_CONFIG" "$NGINX_CONFIG"
    log_success "Fixed nginx configuration installed"
else
    log_error "Fixed nginx configuration not found: $FIXED_CONFIG"
    log_info "Creating basic fixed configuration..."

    cat > "$NGINX_CONFIG" << 'EOF'
server {
    listen 80;
    server_name mytrips-api.bahar.co.il;

    access_log /var/log/nginx/mytrips-api_access.log;
    error_log /var/log/nginx/mytrips-api_error.log;

    # Remove CORS headers from backend to avoid duplicates
    proxy_hide_header Access-Control-Allow-Origin;
    proxy_hide_header Access-Control-Allow-Methods;
    proxy_hide_header Access-Control-Allow-Headers;
    proxy_hide_header Access-Control-Allow-Credentials;

    location ~ ^/(.*)$ {
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, X-Requested-With" always;
            add_header Access-Control-Max-Age 86400 always;
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, X-Requested-With" always;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF
    log_success "Basic fixed configuration created"
fi

# Test nginx configuration
log_info "Testing nginx configuration..."
if nginx -t; then
    log_success "Nginx configuration is valid"
else
    log_error "Nginx configuration test failed"
    log_info "Restoring backup..."
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" "$NGINX_CONFIG"
        log_success "Backup restored"
    fi
    exit 1
fi

# Reload nginx
log_info "Reloading nginx..."
if systemctl reload nginx; then
    log_success "Nginx reloaded successfully"
else
    log_error "Failed to reload nginx"
    exit 1
fi

# Restart backend service
log_info "Restarting backend service..."
if systemctl restart dayplanner-backend; then
    log_success "Backend service restarted"
else
    log_warning "Failed to restart backend service"
fi

# Test the fix
log_info "Testing CORS fix..."

# Determine if HTTPS is configured
if [ -d "/etc/letsencrypt/live/mytrips-api.bahar.co.il" ] || [ -d "/etc/letsencrypt/live/mytrips-api.bahar.co.il-0001" ]; then
    PROTOCOL="https"
    DOMAIN="mytrips-api.bahar.co.il"
    log_info "SSL certificates found, testing HTTPS endpoints..."
else
    PROTOCOL="http"
    DOMAIN="localhost:8000"
    log_info "No SSL certificates found, testing HTTP endpoints..."
fi

# Test preflight request
log_info "Testing preflight request..."
PREFLIGHT_RESPONSE=$(curl -s -X OPTIONS "$PROTOCOL://$DOMAIN/health" \
    -H "Origin: http://localhost:3500" \
    -H "Access-Control-Request-Method: GET" \
    -w "%{http_code}" -o /dev/null)

if [ "$PREFLIGHT_RESPONSE" = "204" ] || [ "$PREFLIGHT_RESPONSE" = "200" ]; then
    log_success "Preflight request successful (HTTP $PREFLIGHT_RESPONSE)"
else
    log_warning "Preflight request returned HTTP $PREFLIGHT_RESPONSE"
fi

# Test actual request
log_info "Testing actual API request..."
API_RESPONSE=$(curl -s "$PROTOCOL://$DOMAIN/health" \
    -H "Origin: http://localhost:3500" \
    -w "%{http_code}" -o /dev/null)

if [ "$API_RESPONSE" = "200" ]; then
    log_success "API request successful (HTTP $API_RESPONSE)"
else
    log_warning "API request returned HTTP $API_RESPONSE"
fi

# Test HTTPS specifically if available
if [ "$PROTOCOL" = "https" ]; then
    log_info "Testing HTTP to HTTPS redirect..."
    REDIRECT_RESPONSE=$(curl -s "http://$DOMAIN/health" \
        -H "Origin: http://localhost:3500" \
        -w "%{http_code}" -o /dev/null)

    if [ "$REDIRECT_RESPONSE" = "301" ] || [ "$REDIRECT_RESPONSE" = "302" ]; then
        log_success "HTTP to HTTPS redirect working (HTTP $REDIRECT_RESPONSE)"
    else
        log_warning "HTTP to HTTPS redirect returned HTTP $REDIRECT_RESPONSE"
    fi
fi

log_success "🎉 CORS fix completed!"
log_info ""
log_info "Next steps:"
if [ "$PROTOCOL" = "https" ]; then
    log_info "1. Test from your frontend: fetch('https://mytrips-api.bahar.co.il/health')"
    log_info "2. Update frontend to use HTTPS: NEXT_PUBLIC_API_BASE_URL=https://mytrips-api.bahar.co.il"
else
    log_info "1. Test from your frontend: fetch('http://mytrips-api.bahar.co.il/health')"
    log_info "2. To enable HTTPS: sudo /opt/dayplanner/deployment/scripts/enable-ssl.sh"
fi
log_info "3. Check browser network tab for CORS headers"
log_info "4. Verify no duplicate Access-Control-Allow-Origin headers"
log_info ""
log_info "If you still have issues:"
log_info "- Check nginx logs: sudo tail -f /var/log/nginx/mytrips-api_error.log"
log_info "- Check backend logs: sudo journalctl -u dayplanner-backend -f"
log_info "- Restore backup if needed: sudo cp $BACKUP_FILE $NGINX_CONFIG"
