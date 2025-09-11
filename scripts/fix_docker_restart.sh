#!/bin/bash

# Docker Restart Fix Script
# Comprehensive solution for Docker restart issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_phase() {
    echo -e "${PURPLE}[PHASE]${NC} $1"
}

# Check Docker installation
check_docker_installation() {
    log_phase "Checking Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return 1
    fi
    
    log_success "Docker CLI is installed"
    
    # Check Docker version
    DOCKER_VERSION=$(docker --version 2>/dev/null || echo "Unknown")
    log_info "Docker version: $DOCKER_VERSION"
}

# Check Docker daemon status
check_docker_daemon() {
    log_phase "Checking Docker Daemon Status"
    
    if docker info &> /dev/null; then
        log_success "Docker daemon is running"
        return 0
    else
        log_warning "Docker daemon is not responding"
        return 1
    fi
}

# Check Docker Desktop status
check_docker_desktop() {
    log_phase "Checking Docker Desktop Status"
    
    if pgrep -f "Docker Desktop" > /dev/null; then
        log_success "Docker Desktop is running"
        
        # Check if it's fully started
        if docker info &> /dev/null; then
            log_success "Docker Desktop is fully operational"
            return 0
        else
            log_warning "Docker Desktop is starting up..."
            return 1
        fi
    else
        log_warning "Docker Desktop is not running"
        return 1
    fi
}

# Start Docker Desktop
start_docker_desktop() {
    log_phase "Starting Docker Desktop"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if [ -d "/Applications/Docker.app" ]; then
            log_info "Starting Docker Desktop on macOS..."
            open -a Docker
            
            # Wait for Docker to start
            log_info "Waiting for Docker Desktop to start (this may take 30-60 seconds)..."
            local timeout=120
            local count=0
            
            while ! docker info &> /dev/null && [ $count -lt $timeout ]; do
                echo -n "."
                sleep 2
                count=$((count + 2))
            done
            echo
            
            if docker info &> /dev/null; then
                log_success "Docker Desktop started successfully"
                return 0
            else
                log_error "Docker Desktop failed to start within $timeout seconds"
                return 1
            fi
        else
            log_error "Docker Desktop not found in /Applications/"
            log_info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
            return 1
        fi
    else
        log_error "Unsupported operating system: $OSTYPE"
        log_info "Please start Docker manually"
        return 1
    fi
}

# Reset Docker daemon
reset_docker_daemon() {
    log_phase "Resetting Docker Daemon"
    
    log_info "Stopping Docker Desktop..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Kill Docker Desktop processes
        pkill -f "Docker Desktop" || true
        pkill -f "com.docker" || true
        
        # Wait a moment
        sleep 5
        
        # Restart Docker Desktop
        start_docker_desktop
    else
        log_warning "Manual Docker restart required on this platform"
        return 1
    fi
}

# Test Docker functionality
test_docker_functionality() {
    log_phase "Testing Docker Functionality"
    
    # Test basic Docker command
    if docker --version &> /dev/null; then
        log_success "Docker CLI working"
    else
        log_error "Docker CLI not working"
        return 1
    fi
    
    # Test Docker daemon
    if docker info &> /dev/null; then
        log_success "Docker daemon accessible"
    else
        log_error "Docker daemon not accessible"
        return 1
    fi
    
    # Test Docker images
    if docker images &> /dev/null; then
        log_success "Docker images command working"
    else
        log_error "Docker images command failed"
        return 1
    fi
    
    # Test Docker containers
    if docker ps &> /dev/null; then
        log_success "Docker containers command working"
    else
        log_error "Docker containers command failed"
        return 1
    fi
    
    log_success "All Docker functionality tests passed"
}

# Fix Docker restart issues
fix_docker_restart() {
    log_phase "Fixing Docker Restart Issues"
    
    # Stop any existing containers
    log_info "Stopping existing containers..."
    docker-compose down 2>/dev/null || true
    
    # Clean up Docker system
    log_info "Cleaning up Docker system..."
    docker system prune -f 2>/dev/null || true
    
    # Remove any stuck containers
    log_info "Removing stuck containers..."
    docker container prune -f 2>/dev/null || true
    
    # Remove unused networks
    log_info "Removing unused networks..."
    docker network prune -f 2>/dev/null || true
    
    log_success "Docker cleanup completed"
}

# Test make restart functionality
test_make_restart() {
    log_phase "Testing Make Restart Functionality"
    
    if [ ! -f "Makefile" ]; then
        log_error "Makefile not found in current directory"
        return 1
    fi
    
    # Check if restart target exists
    if grep -q "^restart:" Makefile; then
        log_success "Make restart target found"
        
        # Test the restart command (dry run)
        log_info "Testing make restart (dry run)..."
        if make -n restart &> /dev/null; then
            log_success "Make restart syntax is valid"
        else
            log_warning "Make restart syntax issues detected"
        fi
    else
        log_error "Make restart target not found in Makefile"
        return 1
    fi
}

# Main execution
main() {
    log_info "🔧 Docker Restart Fix Script"
    log_info "Comprehensive solution for Docker restart issues"
    echo
    
    # Check Docker installation
    if ! check_docker_installation; then
        exit 1
    fi
    echo
    
    # Check Docker daemon
    if ! check_docker_daemon; then
        echo
        
        # Check Docker Desktop
        if ! check_docker_desktop; then
            echo
            
            # Try to start Docker Desktop
            if ! start_docker_desktop; then
                echo
                
                # Try to reset Docker daemon
                log_warning "Attempting to reset Docker daemon..."
                if ! reset_docker_daemon; then
                    log_error "Failed to start Docker. Please try manually:"
                    log_info "1. Quit Docker Desktop completely"
                    log_info "2. Restart Docker Desktop"
                    log_info "3. Wait for it to fully start"
                    log_info "4. Run this script again"
                    exit 1
                fi
            fi
        fi
    fi
    echo
    
    # Test Docker functionality
    if ! test_docker_functionality; then
        log_error "Docker functionality tests failed"
        exit 1
    fi
    echo
    
    # Fix Docker restart issues
    fix_docker_restart
    echo
    
    # Test make restart
    test_make_restart
    echo
    
    log_success "🎉 Docker Restart Fix Complete!"
    echo
    log_info "📋 Next Steps:"
    log_info "1. Try: make restart"
    log_info "2. Or: make down && make up"
    log_info "3. Check: make logs"
    echo
    log_info "✅ Docker should now be working properly for restarts"
}

# Run with error handling
if ! main "$@"; then
    echo
    log_error "❌ Docker restart fix failed"
    log_info "Please check the errors above and try manual Docker restart"
    exit 1
fi
