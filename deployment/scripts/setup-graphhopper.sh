#!/bin/bash

# GraphHopper Self-Hosted Setup Script
# Sets up GraphHopper for routing without Docker

set -e

# Configuration
APP_DIR="/opt/dayplanner"
GRAPHHOPPER_DIR="/opt/graphhopper"
GRAPHHOPPER_VERSION="8.0"
JAVA_OPTS="-Xmx4g -Xms4g"

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

# Install Java
install_java() {
    log_info "Installing Java..."
    
    apt-get update
    apt-get install -y openjdk-11-jre-headless
    
    # Verify Java installation
    java -version
    
    log_success "Java installed successfully"
}

# Download and setup GraphHopper
setup_graphhopper() {
    log_info "Setting up GraphHopper..."
    
    # Create GraphHopper directory
    mkdir -p "$GRAPHHOPPER_DIR"
    cd "$GRAPHHOPPER_DIR"
    
    # Download GraphHopper
    log_info "Downloading GraphHopper $GRAPHHOPPER_VERSION..."
    wget "https://github.com/graphhopper/graphhopper/releases/download/$GRAPHHOPPER_VERSION/graphhopper-web-$GRAPHHOPPER_VERSION.jar" \
         -O graphhopper-web.jar
    
    # Copy configuration
    cp "$APP_DIR/infrastructure/graphhopper/config.yml" "$GRAPHHOPPER_DIR/"
    
    # Create data directory
    mkdir -p "$GRAPHHOPPER_DIR/data"
    mkdir -p "$GRAPHHOPPER_DIR/custom_models"
    
    # Copy custom models if they exist
    if [ -d "$APP_DIR/infrastructure/graphhopper/custom_models" ]; then
        cp -r "$APP_DIR/infrastructure/graphhopper/custom_models/"* "$GRAPHHOPPER_DIR/custom_models/"
    fi
    
    log_success "GraphHopper setup complete"
}

# Download OSM data
download_osm_data() {
    log_info "Available OSM data regions:"
    echo "1) California (recommended for demo)"
    echo "2) Israel"
    echo "3) Europe (large download)"
    echo "4) North America (very large download)"
    echo "5) Skip OSM download (manual setup)"
    
    read -p "Select region (1-5): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            REGION="california"
            OSM_URL="https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
            ;;
        2)
            REGION="israel"
            OSM_URL="https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf"
            ;;
        3)
            REGION="europe"
            OSM_URL="https://download.geofabrik.de/europe-latest.osm.pbf"
            ;;
        4)
            REGION="north-america"
            OSM_URL="https://download.geofabrik.de/north-america-latest.osm.pbf"
            ;;
        5)
            log_warning "Skipping OSM download. You'll need to manually place an OSM file at $GRAPHHOPPER_DIR/data/map.osm.pbf"
            return 0
            ;;
        *)
            log_warning "Invalid selection. Defaulting to California."
            REGION="california"
            OSM_URL="https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
            ;;
    esac
    
    log_info "Downloading OSM data for $REGION..."
    log_warning "This may take a while depending on the region size and your internet connection."
    
    cd "$GRAPHHOPPER_DIR/data"
    wget "$OSM_URL" -O map.osm.pbf
    
    log_success "OSM data downloaded successfully"
}

# Create systemd service
create_service() {
    log_info "Creating GraphHopper systemd service..."
    
    cat > /etc/systemd/system/graphhopper.service << EOF
[Unit]
Description=GraphHopper Routing Service
After=network.target
Wants=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$GRAPHHOPPER_DIR
Environment=JAVA_OPTS=$JAVA_OPTS
ExecStart=/usr/bin/java \$JAVA_OPTS -Ddw.graphhopper.datareader.file=$GRAPHHOPPER_DIR/data/map.osm.pbf -jar $GRAPHHOPPER_DIR/graphhopper-web.jar server $GRAPHHOPPER_DIR/config.yml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=graphhopper

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$GRAPHHOPPER_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=2048

# Health check
TimeoutStartSec=300
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    # Set proper ownership
    chown -R www-data:www-data "$GRAPHHOPPER_DIR"
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable graphhopper.service
    
    log_success "GraphHopper service created and enabled"
}

# Start GraphHopper
start_graphhopper() {
    log_info "Starting GraphHopper service..."
    
    systemctl start graphhopper.service
    
    log_info "Waiting for GraphHopper to initialize (this may take several minutes)..."
    
    # Wait for GraphHopper to be ready
    max_attempts=60
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8989/health > /dev/null 2>&1; then
            log_success "GraphHopper is running and healthy"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log_error "GraphHopper failed to start after $max_attempts attempts"
                log_info "Check logs with: sudo journalctl -u graphhopper.service -f"
                exit 1
            fi
            log_info "Waiting for GraphHopper to be ready... (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    log_success "GraphHopper setup completed successfully!"
}

# Update environment for self-hosted mode
update_environment() {
    log_info "Updating environment configuration for self-hosted GraphHopper..."
    
    if [ -f "$APP_DIR/.env.production" ]; then
        # Update GraphHopper configuration
        sed -i 's/GRAPHHOPPER_MODE=cloud/GRAPHHOPPER_MODE=selfhost/' "$APP_DIR/.env.production"
        sed -i 's|GRAPHHOPPER_BASE_URL=.*|GRAPHHOPPER_BASE_URL=http://localhost:8989|' "$APP_DIR/.env.production"
        
        log_success "Environment updated for self-hosted GraphHopper"
    else
        log_warning "Production environment file not found. Please update manually:"
        log_info "  GRAPHHOPPER_MODE=selfhost"
        log_info "  GRAPHHOPPER_BASE_URL=http://localhost:8989"
    fi
}

# Main setup function
main() {
    log_info "Starting GraphHopper self-hosted setup..."
    
    check_root
    install_java
    setup_graphhopper
    download_osm_data
    create_service
    start_graphhopper
    update_environment
    
    log_success "GraphHopper self-hosted setup completed!"
    log_info "GraphHopper is now running at: http://localhost:8989"
    log_info "Service management commands:"
    log_info "  sudo systemctl status graphhopper"
    log_info "  sudo systemctl restart graphhopper"
    log_info "  sudo journalctl -u graphhopper -f"
}

# Handle script arguments
case "${1:-}" in
    --help)
        echo "Usage: $0 [--help]"
        echo "  --help  Show this help message"
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
