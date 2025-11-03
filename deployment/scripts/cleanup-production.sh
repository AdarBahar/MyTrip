#!/bin/bash

# Production Cleanup Script
# Removes unnecessary files from current production deployment
# Run this on your production server to clean up existing deployment

set -e

# Configuration
APP_DIR="/opt/dayplanner"
BACKUP_DIR="/opt/dayplanner-backups"
LOG_FILE="/var/log/dayplanner/cleanup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create backup before cleanup
create_backup() {
    log_info "Creating backup before cleanup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_path="$BACKUP_DIR/pre-cleanup_$timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup current deployment
    rsync -av "$APP_DIR/" "$backup_path/"
    
    log_success "Backup created at: $backup_path"
}

# Stop services during cleanup
stop_services() {
    log_info "Stopping services for cleanup..."
    
    systemctl stop dayplanner-frontend.service || true
    systemctl stop dayplanner-backend.service || true
    
    log_success "Services stopped"
}

# Start services after cleanup
start_services() {
    log_info "Starting services after cleanup..."
    
    systemctl start dayplanner-backend.service
    sleep 10
    systemctl start dayplanner-frontend.service
    
    log_success "Services started"
}

# Clean up unnecessary files
cleanup_files() {
    log_info "Cleaning up unnecessary files from production deployment..."
    
    cd "$APP_DIR"
    
    # Count files before cleanup
    files_before=$(find . -type f | wc -l)
    
    # Remove documentation files
    log_info "Removing documentation files..."
    find . -name "*.md" -not -path "./deployment/README.md" -delete 2>/dev/null || true
    find . -name "README*" -delete 2>/dev/null || true
    find . -name "CHANGELOG*" -delete 2>/dev/null || true
    find . -name "LICENSE*" -delete 2>/dev/null || true
    
    # Remove test files
    log_info "Removing test files..."
    find . -name "test_*.py" -delete 2>/dev/null || true
    find . -name "*_test.py" -delete 2>/dev/null || true
    find . -name "*.test.js" -delete 2>/dev/null || true
    find . -name "*.spec.js" -delete 2>/dev/null || true
    
    # Remove development scripts
    log_info "Removing development scripts..."
    find . -name "deploy_*.sh" -delete 2>/dev/null || true
    find . -name "test_*.sh" -delete 2>/dev/null || true
    find . -name "debug_*.sh" -delete 2>/dev/null || true
    find . -name "cleanup_*.sh" -delete 2>/dev/null || true
    
    # Remove development directories
    log_info "Removing development directories..."
    rm -rf docs/ 2>/dev/null || true
    rm -rf .github/ 2>/dev/null || true
    rm -rf .vscode/ 2>/dev/null || true
    rm -rf .idea/ 2>/dev/null || true
    rm -rf tests/ 2>/dev/null || true
    rm -rf __tests__/ 2>/dev/null || true
    rm -rf cypress/ 2>/dev/null || true
    rm -rf e2e/ 2>/dev/null || true
    
    # Remove development configuration files
    log_info "Removing development configuration files..."
    rm -f .pre-commit-config.yaml 2>/dev/null || true
    rm -f .secrets.baseline 2>/dev/null || true
    rm -f .editorconfig 2>/dev/null || true
    rm -f .eslintrc* 2>/dev/null || true
    rm -f .prettierrc* 2>/dev/null || true
    rm -f tsconfig.json 2>/dev/null || true
    rm -f jest.config.js 2>/dev/null || true
    
    # Remove temporary and backup files
    log_info "Removing temporary and backup files..."
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.temp" -delete 2>/dev/null || true
    find . -name "*.bak" -delete 2>/dev/null || true
    find . -name "*.backup" -delete 2>/dev/null || true
    find . -name "*.log" -delete 2>/dev/null || true
    
    # Remove OS generated files
    log_info "Removing OS generated files..."
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "Thumbs.db" -delete 2>/dev/null || true
    find . -name "._*" -delete 2>/dev/null || true
    
    # Remove development deployment files
    log_info "Removing development deployment files..."
    rm -rf deployment/production/ 2>/dev/null || true
    rm -rf deployment/user-space/ 2>/dev/null || true
    
    # Remove Python cache files
    log_info "Removing Python cache files..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Remove Node.js development files
    log_info "Removing Node.js development files..."
    find . -name "npm-debug.log*" -delete 2>/dev/null || true
    find . -name "yarn-debug.log*" -delete 2>/dev/null || true
    find . -name "yarn-error.log*" -delete 2>/dev/null || true
    
    # Count files after cleanup
    files_after=$(find . -type f | wc -l)
    files_removed=$((files_before - files_after))
    
    log_success "Cleanup completed!"
    log_info "Files before cleanup: $files_before"
    log_info "Files after cleanup: $files_after"
    log_info "Files removed: $files_removed"
}

# Show disk space savings
show_disk_usage() {
    log_info "Disk usage analysis:"
    du -sh "$APP_DIR" 2>/dev/null || true
}

# Main cleanup function
main() {
    log_info "Starting production deployment cleanup..."
    log_info "Target directory: $APP_DIR"
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    check_root
    create_backup
    stop_services
    cleanup_files
    show_disk_usage
    start_services
    
    log_success "Production cleanup completed successfully!"
    log_info "Backup location: $BACKUP_DIR"
    log_info "Log file: $LOG_FILE"
    
    echo ""
    echo "🎉 Cleanup Summary:"
    echo "   ✅ Unnecessary files removed"
    echo "   ✅ Services restarted"
    echo "   ✅ Backup created"
    echo "   📋 Check log: $LOG_FILE"
}

# Run main function
main "$@"
