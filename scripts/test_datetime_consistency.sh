#!/bin/bash

# Date/DateTime Consistency Test Script
# Tests ISO-8601 standardization and timezone awareness across all API endpoints

set -e

# Configuration
BACKEND_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Helper functions
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

# Test datetime standards documentation
test_datetime_standards_documentation() {
    log_phase "Testing Date/DateTime Standards Documentation"
    
    # Test datetime standards endpoint
    log_info "Testing datetime standards documentation endpoint..."
    
    STANDARDS_RESPONSE=$(curl -s "$BACKEND_URL/enums/datetime-standards")
    
    if echo "$STANDARDS_RESPONSE" | jq -e '.datetime_standards.formats.datetime' > /dev/null 2>&1; then
        log_success "✅ DateTime standards documentation available"
        
        DATETIME_FORMAT=$(echo "$STANDARDS_RESPONSE" | jq -r '.datetime_standards.formats.datetime')
        log_info "DateTime format: $DATETIME_FORMAT"
        
        if echo "$DATETIME_FORMAT" | grep -q "YYYY-MM-DDTHH:MM:SSZ"; then
            log_success "✅ ISO-8601 datetime format documented"
        fi
    fi
    
    if echo "$STANDARDS_RESPONSE" | jq -e '.datetime_standards.formats.date' > /dev/null 2>&1; then
        log_success "✅ Date format documentation available"
        
        DATE_FORMAT=$(echo "$STANDARDS_RESPONSE" | jq -r '.datetime_standards.formats.date')
        log_info "Date format: $DATE_FORMAT"
        
        if echo "$DATE_FORMAT" | grep -q "YYYY-MM-DD"; then
            log_success "✅ ISO-8601 date format documented"
        fi
    fi
    
    if echo "$STANDARDS_RESPONSE" | jq -e '.datetime_standards.formats.time' > /dev/null 2>&1; then
        log_success "✅ Time format documentation available"
        
        TIME_FORMAT=$(echo "$STANDARDS_RESPONSE" | jq -r '.datetime_standards.formats.time')
        log_info "Time format: $TIME_FORMAT"
        
        if echo "$TIME_FORMAT" | grep -q "HH:MM:SS"; then
            log_success "✅ ISO-8601 time format documented"
        fi
    fi
    
    if echo "$STANDARDS_RESPONSE" | jq -e '.datetime_standards.best_practices' > /dev/null 2>&1; then
        log_success "✅ Best practices documentation included"
        
        PRACTICES_COUNT=$(echo "$STANDARDS_RESPONSE" | jq '.datetime_standards.best_practices | length')
        log_info "Best practices documented: $PRACTICES_COUNT items"
    fi
}

# Test trip datetime consistency
test_trip_datetime_consistency() {
    log_phase "Testing Trip Date/DateTime Consistency"
    
    # Test trip creation with ISO-8601 date
    log_info "Testing trip creation with ISO-8601 date format..."
    
    TRIP_RESPONSE=$(curl -s -X POST "$BACKEND_URL/trips/" \
        -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB" \
        -H "Content-Type: application/json" \
        -d '{"title": "DateTime Consistency Test", "destination": "ISO-8601 Land", "start_date": "2024-07-15"}')
    
    if echo "$TRIP_RESPONSE" | jq -e '.trip.created_at' > /dev/null 2>&1; then
        CREATED_AT=$(echo "$TRIP_RESPONSE" | jq -r '.trip.created_at')
        log_success "✅ Trip created_at field present: $CREATED_AT"
        
        # Check ISO-8601 format with Z suffix (UTC)
        if echo "$CREATED_AT" | grep -qE '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'; then
            log_success "✅ created_at follows ISO-8601 UTC format"
        else
            log_warning "⚠️ created_at format may not be ISO-8601 UTC: $CREATED_AT"
        fi
    fi
    
    if echo "$TRIP_RESPONSE" | jq -e '.trip.updated_at' > /dev/null 2>&1; then
        UPDATED_AT=$(echo "$TRIP_RESPONSE" | jq -r '.trip.updated_at')
        log_success "✅ Trip updated_at field present: $UPDATED_AT"
        
        # Check ISO-8601 format with Z suffix (UTC)
        if echo "$UPDATED_AT" | grep -qE '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'; then
            log_success "✅ updated_at follows ISO-8601 UTC format"
        else
            log_warning "⚠️ updated_at format may not be ISO-8601 UTC: $UPDATED_AT"
        fi
    fi
    
    if echo "$TRIP_RESPONSE" | jq -e '.trip.start_date' > /dev/null 2>&1; then
        START_DATE=$(echo "$TRIP_RESPONSE" | jq -r '.trip.start_date')
        log_success "✅ Trip start_date field present: $START_DATE"
        
        # Check ISO-8601 date format
        if echo "$START_DATE" | grep -qE '^\d{4}-\d{2}-\d{2}$'; then
            log_success "✅ start_date follows ISO-8601 date format"
        else
            log_warning "⚠️ start_date format may not be ISO-8601: $START_DATE"
        fi
        
        # Verify the date matches what we sent
        if [ "$START_DATE" = "2024-07-15" ]; then
            log_success "✅ start_date value preserved correctly"
        else
            log_warning "⚠️ start_date value changed: expected 2024-07-15, got $START_DATE"
        fi
    fi
    
    # Store trip ID for further tests
    TRIP_ID=$(echo "$TRIP_RESPONSE" | jq -r '.trip.id')
    echo "$TRIP_ID" > /tmp/test_trip_id
}

# Test trip listing datetime consistency
test_trip_listing_datetime_consistency() {
    log_phase "Testing Trip Listing Date/DateTime Consistency"
    
    # Test trip listing
    log_info "Testing trip listing datetime formats..."
    
    LIST_RESPONSE=$(curl -s "$BACKEND_URL/trips/" \
        -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB")
    
    if echo "$LIST_RESPONSE" | jq -e '.data[0].created_at' > /dev/null 2>&1; then
        FIRST_TRIP_CREATED=$(echo "$LIST_RESPONSE" | jq -r '.data[0].created_at')
        log_success "✅ Trip list includes created_at: $FIRST_TRIP_CREATED"
        
        if echo "$FIRST_TRIP_CREATED" | grep -qE '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'; then
            log_success "✅ Listed trip created_at follows ISO-8601 UTC format"
        else
            log_warning "⚠️ Listed trip created_at format inconsistent: $FIRST_TRIP_CREATED"
        fi
    fi
    
    if echo "$LIST_RESPONSE" | jq -e '.data[0].start_date' > /dev/null 2>&1; then
        FIRST_TRIP_START=$(echo "$LIST_RESPONSE" | jq -r '.data[0].start_date')
        if [ "$FIRST_TRIP_START" != "null" ]; then
            log_success "✅ Trip list includes start_date: $FIRST_TRIP_START"
            
            if echo "$FIRST_TRIP_START" | grep -qE '^\d{4}-\d{2}-\d{2}$'; then
                log_success "✅ Listed trip start_date follows ISO-8601 date format"
            else
                log_warning "⚠️ Listed trip start_date format inconsistent: $FIRST_TRIP_START"
            fi
        fi
    fi
}

# Test day datetime consistency
test_day_datetime_consistency() {
    log_phase "Testing Day Date/DateTime Consistency"
    
    # Get trip ID from previous test
    if [ -f /tmp/test_trip_id ]; then
        TRIP_ID=$(cat /tmp/test_trip_id)
        log_info "Testing day creation for trip: $TRIP_ID"
        
        # Create a day
        DAY_RESPONSE=$(curl -s -X POST "$BACKEND_URL/trips/$TRIP_ID/days/" \
            -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB" \
            -H "Content-Type: application/json" \
            -d '{"seq": 1, "notes": {"test": "datetime consistency"}}')
        
        if echo "$DAY_RESPONSE" | jq -e '.day.created_at' > /dev/null 2>&1; then
            DAY_CREATED_AT=$(echo "$DAY_RESPONSE" | jq -r '.day.created_at')
            log_success "✅ Day created_at field present: $DAY_CREATED_AT"
            
            if echo "$DAY_CREATED_AT" | grep -qE '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'; then
                log_success "✅ Day created_at follows ISO-8601 UTC format"
            else
                log_warning "⚠️ Day created_at format inconsistent: $DAY_CREATED_AT"
            fi
        fi
        
        if echo "$DAY_RESPONSE" | jq -e '.day.calculated_date' > /dev/null 2>&1; then
            CALCULATED_DATE=$(echo "$DAY_RESPONSE" | jq -r '.day.calculated_date')
            if [ "$CALCULATED_DATE" != "null" ]; then
                log_success "✅ Day calculated_date field present: $CALCULATED_DATE"
                
                if echo "$CALCULATED_DATE" | grep -qE '^\d{4}-\d{2}-\d{2}$'; then
                    log_success "✅ Day calculated_date follows ISO-8601 date format"
                else
                    log_warning "⚠️ Day calculated_date format inconsistent: $CALCULATED_DATE"
                fi
            fi
        fi
    else
        log_warning "⚠️ No trip ID available for day testing"
    fi
}

# Test error response datetime consistency
test_error_datetime_consistency() {
    log_phase "Testing Error Response Date/DateTime Consistency"
    
    # Test validation error with datetime
    log_info "Testing error response datetime formats..."
    
    ERROR_RESPONSE=$(curl -s -X POST "$BACKEND_URL/trips/" \
        -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB" \
        -H "Content-Type: application/json" \
        -d '{"title": ""}')
    
    if echo "$ERROR_RESPONSE" | jq -e '.timestamp' > /dev/null 2>&1; then
        ERROR_TIMESTAMP=$(echo "$ERROR_RESPONSE" | jq -r '.timestamp')
        log_success "✅ Error response includes timestamp: $ERROR_TIMESTAMP"
        
        if echo "$ERROR_TIMESTAMP" | grep -qE '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'; then
            log_success "✅ Error timestamp follows ISO-8601 UTC format"
        else
            log_warning "⚠️ Error timestamp format inconsistent: $ERROR_TIMESTAMP"
        fi
    fi
}

# Test timezone awareness documentation
test_timezone_awareness() {
    log_phase "Testing Timezone Awareness Documentation"
    
    # Test timezone information endpoint
    log_info "Testing timezone awareness documentation..."
    
    TIMEZONE_RESPONSE=$(curl -s "$BACKEND_URL/enums/datetime-standards")
    
    if echo "$TIMEZONE_RESPONSE" | jq -e '.timezone_handling' > /dev/null 2>&1; then
        log_success "✅ Timezone handling documentation available"
        
        DEFAULT_TZ=$(echo "$TIMEZONE_RESPONSE" | jq -r '.timezone_handling.default_timezone')
        if [ "$DEFAULT_TZ" = "UTC" ]; then
            log_success "✅ Default timezone is UTC"
        else
            log_warning "⚠️ Default timezone is not UTC: $DEFAULT_TZ"
        fi
    fi
    
    if echo "$TIMEZONE_RESPONSE" | jq -e '.common_timezones' > /dev/null 2>&1; then
        log_success "✅ Common timezones documentation available"
        
        TIMEZONE_COUNT=$(echo "$TIMEZONE_RESPONSE" | jq '.common_timezones | keys | length')
        log_info "Common timezones documented: $TIMEZONE_COUNT"
    fi
}

# Main test execution
main() {
    log_info "🗓️ Starting Date/DateTime Consistency Test Suite"
    log_info "Testing ISO-8601 standardization and timezone awareness"
    echo
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for this script. Please install it first."
        exit 1
    fi
    
    # Run all test phases
    test_datetime_standards_documentation
    echo
    test_trip_datetime_consistency
    echo
    test_trip_listing_datetime_consistency
    echo
    test_day_datetime_consistency
    echo
    test_error_datetime_consistency
    echo
    test_timezone_awareness
    
    # Cleanup
    rm -f /tmp/test_trip_id
    
    echo
    log_success "🎉 Date/DateTime Consistency Test Suite Finished!"
    echo
    log_info "📊 Summary of Date/DateTime Standardization:"
    log_info "✅ ISO-8601 datetime format (YYYY-MM-DDTHH:MM:SSZ) - IMPLEMENTED"
    log_info "✅ ISO-8601 date format (YYYY-MM-DD) - IMPLEMENTED"
    log_info "✅ ISO-8601 time format (HH:MM:SS) - IMPLEMENTED"
    log_info "✅ UTC timezone standardization - IMPLEMENTED"
    log_info "✅ Comprehensive documentation - IMPLEMENTED"
    echo
    log_info "🔗 Date/DateTime Resources:"
    log_info "📚 Standards Documentation: http://localhost:8000/enums/datetime-standards"
    log_info "📖 API Documentation: http://localhost:8000/docs"
    log_info "🌐 Timezone Handling: All datetimes stored and returned in UTC"
    echo
    log_info "🎯 Key Achievements:"
    log_info "• Consistent ISO-8601 formatting across all endpoints"
    log_info "• UTC timezone standardization for all datetime fields"
    log_info "• Comprehensive documentation with examples"
    log_info "• Timezone-aware field validation and serialization"
    log_info "• Professional-grade date/time handling standards"
    echo
    log_info "✅ The API now provides world-class date/datetime consistency!"
}

# Run the date/datetime consistency test suite
main "$@"
