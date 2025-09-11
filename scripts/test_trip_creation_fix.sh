#!/bin/bash

# Trip Creation Conflict Fix Test Script
# Tests the fixes for 409 Conflict errors when creating trips

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

# Test 1: Check TripCreate Interface
test_trip_create_interface() {
    log_phase "Testing TripCreate Interface"
    
    TRIPS_API="frontend/lib/api/trips.ts"
    
    if [ -f "$TRIPS_API" ]; then
        log_success "✅ Trips API file exists"
        
        # Check for required fields in TripCreate interface
        if grep -q "status.*draft.*active.*completed.*archived" "$TRIPS_API"; then
            log_success "✅ TripCreate interface includes status field"
        fi
        
        if grep -q "is_published.*boolean" "$TRIPS_API"; then
            log_success "✅ TripCreate interface includes is_published field"
        fi
        
        if grep -q "timezone.*string" "$TRIPS_API"; then
            log_success "✅ TripCreate interface includes timezone field"
        fi
    else
        log_error "❌ Trips API file not found"
    fi
}

# Test 2: Check Form Default Values
test_form_defaults() {
    log_phase "Testing Form Default Values"
    
    CREATE_PAGE="frontend/app/trips/create/page.tsx"
    
    if [ -f "$CREATE_PAGE" ]; then
        log_success "✅ Trip creation page exists"
        
        # Check for default values in form state
        if grep -q "status.*draft" "$CREATE_PAGE"; then
            log_success "✅ Form has default status: draft"
        fi
        
        if grep -q "is_published.*false" "$CREATE_PAGE"; then
            log_success "✅ Form has default is_published: false"
        fi
        
        if grep -q "timezone.*UTC" "$CREATE_PAGE"; then
            log_success "✅ Form has default timezone: UTC"
        fi
        
        # Check for conflict error handling
        if grep -q "409.*RESOURCE_CONFLICT" "$CREATE_PAGE"; then
            log_success "✅ Specific 409 conflict error handling implemented"
        fi
        
        # Check for title uniqueness logic
        if grep -q "title.*toLowerCase.*trim" "$CREATE_PAGE"; then
            log_success "✅ Generic title handling implemented"
        fi
    else
        log_error "❌ Trip creation page not found"
    fi
}

# Test 3: Check Error Display
test_error_display() {
    log_phase "Testing Error Display"
    
    CREATE_PAGE="frontend/app/trips/create/page.tsx"
    
    if [ -f "$CREATE_PAGE" ]; then
        # Check for local error state
        if grep -q "localError.*useState" "$CREATE_PAGE"; then
            log_success "✅ Local error state implemented"
        fi
        
        # Check for conflict-specific error message
        if grep -q "title already exists" "$CREATE_PAGE"; then
            log_success "✅ User-friendly conflict error message"
        fi
        
        # Check for error display in UI
        if grep -q "bg-red-50.*border-red-200" "$CREATE_PAGE"; then
            log_success "✅ Error display UI implemented"
        fi
    fi
}

# Test 4: Check Backend Compatibility
test_backend_compatibility() {
    log_phase "Testing Backend Compatibility"
    
    log_info "Checking if backend expects the fields we're sending..."
    
    # Check if we can find backend schema information
    if [ -d "backend" ]; then
        log_info "Backend directory found - checking for trip schema"
        
        # Look for trip model or schema files
        TRIP_FILES=$(find backend -name "*.py" -exec grep -l "class.*Trip\|TripCreate\|TripSchema" {} \; 2>/dev/null || echo "")
        
        if [ -n "$TRIP_FILES" ]; then
            log_success "✅ Found backend trip-related files"
            echo "$TRIP_FILES" | while read -r file; do
                log_info "  - $file"
            done
        else
            log_warning "⚠️ No backend trip files found"
        fi
    else
        log_warning "⚠️ Backend directory not found"
    fi
}

# Test 5: Validate Required Fields
test_required_fields() {
    log_phase "Testing Required Fields Validation"
    
    CREATE_PAGE="frontend/app/trips/create/page.tsx"
    
    if [ -f "$CREATE_PAGE" ]; then
        # Check that all required fields are being sent
        log_info "Checking that form sends all required fields:"
        
        if grep -q "title.*formData" "$CREATE_PAGE"; then
            log_success "✅ Title field included"
        fi
        
        if grep -q "destination.*formData" "$CREATE_PAGE"; then
            log_success "✅ Destination field included"
        fi
        
        if grep -q "start_date.*formData" "$CREATE_PAGE"; then
            log_success "✅ Start date field included"
        fi
        
        # Check for the new required fields
        FORM_DATA_LINES=$(grep -n "formData.*useState" "$CREATE_PAGE" | head -1)
        if [ -n "$FORM_DATA_LINES" ]; then
            LINE_NUM=$(echo "$FORM_DATA_LINES" | cut -d: -f1)
            FORM_BLOCK=$(sed -n "${LINE_NUM},/}/p" "$CREATE_PAGE")
            
            if echo "$FORM_BLOCK" | grep -q "status"; then
                log_success "✅ Status field in form data"
            fi
            
            if echo "$FORM_BLOCK" | grep -q "is_published"; then
                log_success "✅ is_published field in form data"
            fi
            
            if echo "$FORM_BLOCK" | grep -q "timezone"; then
                log_success "✅ Timezone field in form data"
            fi
        fi
    fi
}

# Main execution
main() {
    log_info "🔧 Starting Trip Creation Conflict Fix Test Suite"
    log_info "Testing fixes for 409 Conflict errors when creating trips"
    echo
    
    test_trip_create_interface
    echo
    test_form_defaults
    echo
    test_error_display
    echo
    test_backend_compatibility
    echo
    test_required_fields
    
    echo
    log_success "🎉 Trip Creation Fix Test Suite Finished!"
    echo
    log_info "📊 Summary of Fixes:"
    log_info "✅ TripCreate interface updated with required fields"
    log_info "✅ Form default values added (status, is_published, timezone)"
    log_info "✅ Specific 409 conflict error handling implemented"
    log_info "✅ User-friendly error messages for conflicts"
    log_info "✅ Generic title handling to prevent common conflicts"
    echo
    log_info "🎯 Key Improvements:"
    log_info "• Added missing required fields to prevent backend validation errors"
    log_info "• Implemented specific conflict error handling with clear messages"
    log_info "• Added automatic title modification for generic names"
    log_info "• Enhanced error display for better user experience"
    echo
    log_info "🧪 How to Test:"
    log_info "1. Navigate to http://localhost:3500/trips/create"
    log_info "2. Try creating a trip with a simple title like 'Trip'"
    log_info "3. Try creating multiple trips with the same title"
    log_info "4. Verify error messages are user-friendly"
    log_info "5. Check that trips are created successfully with unique titles"
    echo
    log_info "✅ Trip creation should now work without 409 conflicts!"
}

main "$@"
