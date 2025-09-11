#!/bin/bash

# PRODUCTION Database Cleanup Runner
# ⚠️  WARNING: This operates on the PRODUCTION database!

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

# Production database configuration
DB_HOST="srv1135.hstgr.io"
DB_PORT="3306"
DB_NAME="u181637338_dayplanner"
DB_USER="u181637338_dayplanner"
DB_PASS="xbZeSoREl%c63Ttq"

# Check if MySQL client is available
check_mysql_client() {
    log_phase "Checking MySQL Client"
    
    if ! command -v mysql &> /dev/null; then
        log_error "MySQL client not found. Please install MySQL client."
        exit 1
    fi
    
    log_success "✅ MySQL client found"
}

# Test production database connection
test_production_connection() {
    log_phase "Testing PRODUCTION Database Connection"
    
    log_warning "⚠️  Connecting to PRODUCTION database:"
    log_info "  Host: $DB_HOST"
    log_info "  Database: $DB_NAME"
    log_info "  User: $DB_USER"
    
    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" -e "SELECT 1;" "$DB_NAME" &> /dev/null; then
        log_error "Cannot connect to PRODUCTION MySQL database: $DB_NAME"
        log_error "Please check your credentials and network connection."
        exit 1
    fi
    
    log_success "✅ Connected to PRODUCTION database"
}

# Show current production database state
show_production_state() {
    log_phase "Current PRODUCTION Database State"
    
    log_info "Current trip data in PRODUCTION:"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" << 'EOF'
SELECT 'Current Trip Data Count in PRODUCTION:' as info;
SELECT 
    'trips' as table_name, 
    COUNT(*) as records 
FROM trips
UNION ALL
SELECT 'trip_members', COUNT(*) FROM trip_members
UNION ALL  
SELECT 'days', COUNT(*) FROM days
UNION ALL
SELECT 'stops', COUNT(*) FROM stops
UNION ALL
SELECT 'route_versions', COUNT(*) FROM route_versions
UNION ALL
SELECT 'route_legs', COUNT(*) FROM route_legs
UNION ALL
SELECT 'pins', COUNT(*) FROM pins
UNION ALL
SELECT 'places (trip-owned)', COUNT(*) FROM places WHERE owner_type = 'trip'
UNION ALL
SELECT 'users (preserved)', COUNT(*) FROM users;

SELECT 'Recent trips in PRODUCTION:' as info;
SELECT id, slug, title, created_at FROM trips ORDER BY created_at DESC LIMIT 5;
EOF
}

# Run the production cleanup
run_production_cleanup() {
    log_phase "PRODUCTION Database Cleanup"
    
    log_error "🚨 CRITICAL WARNING: PRODUCTION DATABASE CLEANUP 🚨"
    log_warning "This will permanently delete ALL trip-related data from:"
    log_warning "  Database: $DB_NAME"
    log_warning "  Host: $DB_HOST"
    echo
    log_info "The following will be preserved:"
    log_info "  - All users and user settings"
    log_info "  - User-owned and system-owned places"
    log_info "  - All non-trip related data"
    echo
    log_error "This action CANNOT be undone!"
    echo
    
    read -p "Type 'DELETE ALL PRODUCTION TRIPS' to confirm: " confirmation
    
    if [ "$confirmation" != "DELETE ALL PRODUCTION TRIPS" ]; then
        log_error "PRODUCTION cleanup cancelled. No changes made."
        exit 1
    fi
    
    log_info "Starting PRODUCTION cleanup process..."
    
    # Run the SQL cleanup script
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" << 'EOF'
-- Start transaction
START TRANSACTION;

-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Clean in dependency order
DELETE FROM route_legs;
DELETE FROM route_versions;  
DELETE FROM stops;
DELETE FROM pins;
DELETE FROM days;
DELETE FROM trip_members;
DELETE FROM places WHERE owner_type = 'trip';
DELETE FROM trips;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Commit the changes
COMMIT;

SELECT 'PRODUCTION cleanup completed successfully!' as result;
EOF

    if [ $? -eq 0 ]; then
        log_success "✅ PRODUCTION database cleanup completed successfully!"
    else
        log_error "❌ PRODUCTION database cleanup failed!"
        exit 1
    fi
}

# Verify production cleanup
verify_production_cleanup() {
    log_phase "Verifying PRODUCTION Cleanup"
    
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" << 'EOF'
SELECT 'PRODUCTION Verification Results:' as info;

SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM trips) = 0 
         AND (SELECT COUNT(*) FROM trip_members) = 0
         AND (SELECT COUNT(*) FROM days) = 0
         AND (SELECT COUNT(*) FROM stops) = 0
         AND (SELECT COUNT(*) FROM route_versions) = 0
         AND (SELECT COUNT(*) FROM route_legs) = 0
         AND (SELECT COUNT(*) FROM pins) = 0
        THEN '✅ CLEANUP SUCCESSFUL - All trip tables are empty'
        ELSE '❌ CLEANUP INCOMPLETE - Some trip data remains'
    END as status;

SELECT 
    CONCAT('👥 Users preserved: ', COUNT(*)) as preserved_users
FROM users;

SELECT 
    CONCAT('📍 Non-trip places preserved: ', COUNT(*)) as preserved_places
FROM places 
WHERE owner_type != 'trip';
EOF
}

# Main execution
main() {
    log_error "🚨 PRODUCTION Database Cleanup Tool 🚨"
    echo "=" * 60
    log_warning "⚠️  WARNING: This operates on the PRODUCTION database!"
    echo "=" * 60
    echo
    
    check_mysql_client
    echo
    test_production_connection
    echo
    show_production_state
    echo
    run_production_cleanup
    echo
    verify_production_cleanup
    
    echo
    log_success "🎉 PRODUCTION database cleanup completed!"
    echo
    log_info "🚀 Next Steps:"
    log_info "1. Restart your backend server"
    log_info "2. Clear browser cache"
    log_info "3. Try creating a new trip at http://localhost:3500/trips/create"
    log_info "4. The 409 conflict errors should be resolved"
    echo
    log_info "✅ Your PRODUCTION database is now clean and ready for fresh trip data!"
}

# Run the cleanup
main "$@"
