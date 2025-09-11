#!/bin/bash

# Clear Frontend Cache Script
# Clears browser cache, local storage, and restarts servers

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

# Clear Next.js cache
clear_nextjs_cache() {
    log_phase "Clearing Next.js Cache"
    
    if [ -d "frontend/.next" ]; then
        rm -rf frontend/.next
        log_success "✅ Cleared Next.js build cache"
    else
        log_info "No Next.js cache found"
    fi
    
    if [ -d "frontend/node_modules/.cache" ]; then
        rm -rf frontend/node_modules/.cache
        log_success "✅ Cleared Node.js cache"
    else
        log_info "No Node.js cache found"
    fi
}

# Show database configuration
show_db_config() {
    log_phase "Current Database Configuration"
    
    log_info "Backend will connect to:"
    grep "DB_HOST\|DB_NAME\|DB_USER" .env | while read line; do
        log_info "  $line"
    done
}

# Verify local database
verify_local_db() {
    log_phase "Verifying Local Database"
    
    if mysql -u root dayplanner -e "SELECT COUNT(*) as trip_count FROM trips;" 2>/dev/null; then
        TRIP_COUNT=$(mysql -u root dayplanner -e "SELECT COUNT(*) FROM trips;" -s)
        log_success "✅ Local database connected"
        log_info "Current trips in local database: $TRIP_COUNT"
    else
        log_error "❌ Cannot connect to local database"
        log_error "Make sure MySQL is running and 'dayplanner' database exists"
        exit 1
    fi
}

# Instructions for browser cache
show_browser_instructions() {
    log_phase "Browser Cache Instructions"
    
    log_warning "⚠️  You need to clear your browser cache manually:"
    echo
    log_info "🌐 Chrome/Edge:"
    log_info "  1. Press F12 to open Developer Tools"
    log_info "  2. Right-click the refresh button"
    log_info "  3. Select 'Empty Cache and Hard Reload'"
    echo
    log_info "🦊 Firefox:"
    log_info "  1. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
    log_info "  2. Or go to Settings > Privacy & Security > Clear Data"
    echo
    log_info "🧭 Safari:"
    log_info "  1. Press Cmd+Option+E to empty caches"
    log_info "  2. Or Develop > Empty Caches"
    echo
    log_info "💾 Alternative - Use Incognito/Private Mode:"
    log_info "  Open http://localhost:3500 in a private/incognito window"
}

# Main execution
main() {
    log_info "🧹 Frontend Cache Clear Tool"
    echo "=" * 50
    echo
    
    show_db_config
    echo
    verify_local_db
    echo
    clear_nextjs_cache
    echo
    show_browser_instructions
    
    echo
    log_success "🎉 Cache clearing completed!"
    echo
    log_info "🚀 Next Steps:"
    log_info "1. Restart your backend server (if running)"
    log_info "2. Restart your frontend server (if running)"
    log_info "3. Clear browser cache (see instructions above)"
    log_info "4. Navigate to http://localhost:3500/trips"
    log_info "5. Should show empty trips list"
    echo
    log_info "✅ Your application should now use the clean local database!"
}

# Run the cache clear
main "$@"
