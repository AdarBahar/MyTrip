#!/bin/bash

# SSL Certificate Setup Script for MyTrips API
# This script sets up SSL certificates and configures HTTPS

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

# Configuration
DOMAIN="mytrips-api.bahar.co.il"
EMAIL="${SSL_EMAIL:-admin@bahar.co.il}"

log_info "🔒 Setting up SSL certificates for $DOMAIN..."

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    log_info "Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    log_success "Certbot installed"
fi

# Check if certificates already exist
if [ -d "/etc/letsencrypt/live/$DOMAIN" ] || [ -d "/etc/letsencrypt/live/$DOMAIN-0001" ]; then
    log_warning "SSL certificates already exist for $DOMAIN"

    # Show existing certificates
    certbot certificates | grep -A 10 "$DOMAIN" || true

    read -p "Do you want to renew/recreate certificates? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping certificate creation"
        SKIP_CERT_CREATION=true
    fi
fi

# Create SSL certificates
if [ "$SKIP_CERT_CREATION" != "true" ]; then
    log_info "Creating SSL certificates for $DOMAIN..."

    # Stop nginx temporarily to avoid conflicts
    systemctl stop nginx || true

    # Get SSL certificate
    if certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive; then
        log_success "SSL certificates created successfully"
    else
        log_error "Failed to create SSL certificates"
        systemctl start nginx || true
        exit 1
    fi

    # Start nginx
    systemctl start nginx
fi

# Find certificate directory
if [ -d "/etc/letsencrypt/live/$DOMAIN-0001" ]; then
    CERT_DIR="$DOMAIN-0001"
elif [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    CERT_DIR="$DOMAIN"
else
    log_error "SSL certificates not found after creation"
    exit 1
fi

log_info "Using certificate directory: $CERT_DIR"

# Backup current nginx configuration
NGINX_CONFIG="/etc/nginx/sites-available/mytrips-api"
BACKUP_FILE="/etc/nginx/sites-available/mytrips-api.backup.ssl.$(date +%Y%m%d_%H%M%S)"

if [ -f "$NGINX_CONFIG" ]; then
    log_info "Backing up current nginx configuration..."
    cp "$NGINX_CONFIG" "$BACKUP_FILE"
    log_success "Backup created: $BACKUP_FILE"
fi

# Create HTTPS-enabled nginx configuration
log_info "Creating HTTPS-enabled nginx configuration..."

cat > "$NGINX_CONFIG" << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;

    # Redirect HTTP to HTTPS
    if (\$host = $DOMAIN) {
        return 301 https://\$host\$request_uri;
    }
    return 404;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name $DOMAIN;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/$CERT_DIR/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$CERT_DIR/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Logging
    access_log /var/log/nginx/mytrips-api_access.log;
    error_log /var/log/nginx/mytrips-api_error.log;

    # Remove CORS headers from backend to avoid duplicates
    proxy_hide_header Access-Control-Allow-Origin;
    proxy_hide_header Access-Control-Allow-Methods;
    proxy_hide_header Access-Control-Allow-Headers;
    proxy_hide_header Access-Control-Allow-Credentials;

    # Handle all requests
    location ~ ^/(.*)\$ {
        if (\$request_method = 'OPTIONS') {
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, X-Requested-With" always;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

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

# Set up automatic certificate renewal
log_info "Setting up automatic certificate renewal..."
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    log_success "Automatic renewal configured"
else
    log_info "Automatic renewal already configured"
fi

# Test HTTPS
log_info "Testing HTTPS configuration..."
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" | grep -q "200"; then
    log_success "HTTPS is working correctly"
else
    log_warning "HTTPS test failed, but configuration was applied"
fi

log_success "🎉 SSL setup completed!"
log_info ""
log_info "Your API is now available at:"
log_info "  https://$DOMAIN"
log_info ""
log_info "Certificate details:"
certbot certificates | grep -A 10 "$DOMAIN" || true
log_info ""
log_info "Certificate will auto-renew. Check renewal with:"
log_info "  sudo certbot renew --dry-run"
