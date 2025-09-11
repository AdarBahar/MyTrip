#!/bin/bash

# Fix Table Names Script
# Renames MyTrips_ prefixed tables to match backend expectations

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

# Database configuration for local MySQL
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="dayplanner"
DB_USER="root"
DB_PASS=""

# Check MySQL connection
check_mysql() {
    log_phase "Checking MySQL Connection"
    
    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} -e "SELECT 1;" "$DB_NAME" &> /dev/null; then
        log_error "Cannot connect to local MySQL database: $DB_NAME"
        log_error "Make sure MySQL is running and the database exists."
        exit 1
    fi
    
    log_success "✅ Connected to local MySQL database: $DB_NAME"
}

# Show current table structure
show_current_tables() {
    log_phase "Current Database Tables"
    
    log_info "Tables with MyTrips_ prefix:"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" -e "SHOW TABLES LIKE 'MyTrips_%';"
    
    log_info "Tables without prefix:"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" -e "SHOW TABLES;" | grep -v "MyTrips_" | grep -v "Tables_in_" || echo "None found"
}

# Rename tables
rename_tables() {
    log_phase "Renaming Tables to Match Backend Schema"
    
    log_warning "⚠️  This will rename tables to match the backend expectations:"
    log_info "  MyTrips_Users      -> users"
    log_info "  MyTrips_Trips      -> trips"
    log_info "  MyTrips_TripMembers -> trip_members"
    log_info "  MyTrips_Days       -> days"
    log_info "  MyTrips_Stops      -> stops"
    log_info "  MyTrips_Routes     -> route_versions"
    log_info "  MyTrips_Legs       -> route_legs"
    log_info "  MyTrips_Pins       -> pins"
    echo
    
    read -p "Type 'RENAME TABLES' to confirm: " confirmation
    
    if [ "$confirmation" != "RENAME TABLES" ]; then
        log_error "Table rename cancelled. No changes made."
        exit 1
    fi
    
    log_info "Starting table rename process..."
    
    # Run the rename script
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" << 'EOF'
-- Start transaction
START TRANSACTION;

-- Rename tables in dependency order
RENAME TABLE MyTrips_Users TO users;
RENAME TABLE MyTrips_Trips TO trips;
RENAME TABLE MyTrips_TripMembers TO trip_members;
RENAME TABLE MyTrips_Days TO days;
RENAME TABLE MyTrips_Stops TO stops;
RENAME TABLE MyTrips_Routes TO route_versions;
RENAME TABLE MyTrips_Legs TO route_legs;
RENAME TABLE MyTrips_Pins TO pins;

-- Commit the changes
COMMIT;

SELECT 'Table rename completed successfully!' as result;
EOF

    if [ $? -eq 0 ]; then
        log_success "✅ Tables renamed successfully!"
    else
        log_error "❌ Table rename failed!"
        exit 1
    fi
}

# Verify rename
verify_rename() {
    log_phase "Verifying Table Rename"
    
    log_info "Checking for required tables:"
    
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" << 'EOF'
SELECT 'Required tables check:' as info;

SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('trips', 'users', 'days', 'stops', 'route_versions', 'route_legs', 'pins', 'trip_members')
        THEN '✅ FOUND'
        ELSE '📋 OTHER'
    END as status
FROM information_schema.tables 
WHERE table_schema = 'dayplanner'
AND table_name IN ('trips', 'users', 'days', 'stops', 'route_versions', 'route_legs', 'pins', 'trip_members')
ORDER BY table_name;

SELECT 'Record counts:' as info;

SELECT 'trips' as table_name, COUNT(*) as records FROM trips
UNION ALL
SELECT 'users', COUNT(*) FROM users
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
SELECT 'pins', COUNT(*) FROM pins;
EOF
}

# Test backend connection
test_backend_connection() {
    log_phase "Testing Backend Connection"
    
    log_info "The backend should now be able to connect to the renamed tables."
    log_info "Try starting your backend server and creating a trip!"
    
    # Check if we can query the trips table
    TRIP_COUNT=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" -e "SELECT COUNT(*) FROM trips;" -s)
    log_info "Current trips in database: $TRIP_COUNT"
}

# Main execution
main() {
    log_info "🔧 Table Name Fix Tool"
    echo "=" * 50
    echo
    
    check_mysql
    echo
    show_current_tables
    echo
    rename_tables
    echo
    verify_rename
    echo
    test_backend_connection
    
    echo
    log_success "🎉 Table rename completed!"
    echo
    log_info "🚀 Next Steps:"
    log_info "1. Start your backend server"
    log_info "2. Try creating a new trip at http://localhost:3500/trips/create"
    log_info "3. The 409 conflict errors should be resolved"
    echo
    log_info "✅ Your database schema now matches the backend expectations!"
}

# Run the fix
main "$@"
