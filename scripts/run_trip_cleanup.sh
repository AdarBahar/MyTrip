#!/bin/bash

# Trip Database Cleanup Runner
# Safely removes all trip-related data from the production MySQL database

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

# Database configuration
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="dayplanner"
DB_USER="root"
DB_PASS=""

# Check if MySQL is running
check_mysql() {
    log_phase "Checking MySQL Connection"
    
    if ! command -v mysql &> /dev/null; then
        log_error "MySQL client not found. Please install MySQL client."
        exit 1
    fi
    
    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} -e "SELECT 1;" "$DB_NAME" &> /dev/null; then
        log_error "Cannot connect to MySQL database: $DB_NAME"
        log_error "Please check your database configuration and ensure MySQL is running."
        exit 1
    fi
    
    log_success "✅ Connected to MySQL database: $DB_NAME"
}

# Show current database state
show_current_state() {
    log_phase "Current Database State"
    
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" << 'EOF'
SELECT 'Current Trip Data Count:' as info;
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
EOF
}

# Run the cleanup
run_cleanup() {
    log_phase "Running Database Cleanup"
    
    log_warning "⚠️  WARNING: This will permanently delete ALL trip-related data!"
    log_info "The following will be preserved:"
    log_info "  - All users and user settings"
    log_info "  - User-owned and system-owned places"
    log_info "  - All non-trip related data"
    echo
    
    read -p "Type 'DELETE ALL TRIPS' to confirm: " confirmation
    
    if [ "$confirmation" != "DELETE ALL TRIPS" ]; then
        log_error "Cleanup cancelled. No changes made."
        exit 1
    fi
    
    log_info "Starting cleanup process..."
    
    # Run the SQL cleanup script
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" << 'EOF'
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

SELECT 'Cleanup completed successfully!' as result;
EOF

    if [ $? -eq 0 ]; then
        log_success "✅ Database cleanup completed successfully!"
    else
        log_error "❌ Database cleanup failed!"
        exit 1
    fi
}

# Verify cleanup
verify_cleanup() {
    log_phase "Verifying Cleanup"
    
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" << 'EOF'
SELECT 'Verification Results:' as info;

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
    log_info "🧹 Trip Database Cleanup Tool"
    echo "=" * 50
    echo
    
    check_mysql
    echo
    show_current_state
    echo
    run_cleanup
    echo
    verify_cleanup
    
    echo
    log_success "🎉 Database cleanup completed!"
    echo
    log_info "🚀 Next Steps:"
    log_info "1. Restart your backend server"
    log_info "2. Try creating a new trip at http://localhost:3500/trips/create"
    log_info "3. The 409 conflict errors should be resolved"
    echo
    log_info "✅ Your database is now clean and ready for fresh trip data!"
}

# Run the cleanup
main "$@"
