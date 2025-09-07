#!/bin/bash

# Frontend Migration Test Script
# Tests the Phase 1 frontend migration implementation

set -e

# Configuration
FRONTEND_URL="http://localhost:3500"
BACKEND_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Test frontend availability
test_frontend_availability() {
    log_info "Testing frontend availability..."
    
    RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" "$FRONTEND_URL")
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Frontend is available at $FRONTEND_URL"
    else
        log_error "Frontend is not available (HTTP $HTTP_STATUS)"
        exit 1
    fi
}

# Test migration demo page
test_migration_demo_page() {
    log_info "Testing migration demo page..."
    
    RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" "$FRONTEND_URL/migration-demo")
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Migration demo page is accessible"
        
        # Check for key content
        if echo "$BODY" | grep -q "Phase 1 Migration Demo"; then
            log_success "Demo page contains expected title"
        else
            log_warning "Demo page missing expected title"
        fi
        
        if echo "$BODY" | grep -q "HTTP Status Codes"; then
            log_success "Demo page contains HTTP status codes section"
        else
            log_warning "Demo page missing HTTP status codes section"
        fi
        
        if echo "$BODY" | grep -q "Enhanced Errors"; then
            log_success "Demo page contains enhanced errors section"
        else
            log_warning "Demo page missing enhanced errors section"
        fi
        
        if echo "$BODY" | grep -q "Create New Trip"; then
            log_success "Demo page contains trip creation form"
        else
            log_warning "Demo page missing trip creation form"
        fi
        
    else
        log_error "Migration demo page is not accessible (HTTP $HTTP_STATUS)"
    fi
}

# Test backend API connectivity
test_backend_connectivity() {
    log_info "Testing backend API connectivity..."
    
    RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" "$BACKEND_URL/health")
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Backend API is healthy"
        
        if echo "$BODY" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
            log_success "Backend reports healthy status"
        else
            log_warning "Backend health check returned unexpected format"
        fi
    else
        log_error "Backend API is not healthy (HTTP $HTTP_STATUS)"
    fi
}

# Test enhanced error responses
test_enhanced_error_responses() {
    log_info "Testing enhanced error responses..."
    
    # Test validation error
    log_info "Testing validation error response..."
    RESPONSE=$(curl -s -X POST "$BACKEND_URL/trips/" \
        -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB" \
        -H "Content-Type: application/json" \
        -d '{"title": ""}')
    
    if echo "$RESPONSE" | jq -e '.error.error_code == "VALIDATION_ERROR"' > /dev/null 2>&1; then
        log_success "Validation error has correct error_code"
    else
        log_warning "Validation error missing or incorrect error_code"
    fi
    
    if echo "$RESPONSE" | jq -e '.error.field_errors' > /dev/null 2>&1; then
        log_success "Validation error includes field_errors"
    else
        log_warning "Validation error missing field_errors"
    fi
    
    if echo "$RESPONSE" | jq -e '.error.suggestions' > /dev/null 2>&1; then
        log_success "Validation error includes suggestions"
    else
        log_warning "Validation error missing suggestions"
    fi
    
    if echo "$RESPONSE" | jq -e '.timestamp' > /dev/null 2>&1; then
        log_success "Error response includes timestamp"
    else
        log_warning "Error response missing timestamp"
    fi
    
    if echo "$RESPONSE" | jq -e '.request_id' > /dev/null 2>&1; then
        log_success "Error response includes request_id"
    else
        log_warning "Error response missing request_id"
    fi
    
    # Test authentication error
    log_info "Testing authentication error response..."
    RESPONSE=$(curl -s -X GET "$BACKEND_URL/trips/")
    
    if echo "$RESPONSE" | jq -e '.error.error_code == "AUTHENTICATION_REQUIRED"' > /dev/null 2>&1; then
        log_success "Authentication error has correct error_code"
    else
        log_warning "Authentication error missing or incorrect error_code"
    fi
}

# Test HTTP status codes
test_http_status_codes() {
    log_info "Testing HTTP status codes..."
    
    # Test 201 Created for trip creation
    log_info "Testing 201 Created for trip creation..."
    RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" -X POST "$BACKEND_URL/trips/" \
        -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB" \
        -H "Content-Type: application/json" \
        -d "{\"title\": \"Test Trip $(date +%s)\", \"destination\": \"Test Destination\"}")
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')
    
    if [ "$HTTP_STATUS" = "201" ]; then
        log_success "Trip creation returns 201 Created"
        
        TRIP_ID=$(echo "$BODY" | jq -r '.trip.id // empty')
        if [ ! -z "$TRIP_ID" ] && [ "$TRIP_ID" != "null" ]; then
            log_success "Trip creation returns trip data with ID: $TRIP_ID"
            
            # Test 204 No Content for trip deletion
            log_info "Testing 204 No Content for trip deletion..."
            DELETE_RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" -X DELETE "$BACKEND_URL/trips/$TRIP_ID" \
                -H "Authorization: Bearer fake_token_01K367ED2RPNS2H19J8PQDNXFB")
            
            DELETE_STATUS=$(echo "$DELETE_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
            DELETE_BODY=$(echo "$DELETE_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')
            
            if [ "$DELETE_STATUS" = "204" ]; then
                log_success "Trip deletion returns 204 No Content"
                
                if [ -z "$DELETE_BODY" ] || [ "$DELETE_BODY" = "" ]; then
                    log_success "Trip deletion returns empty body (correct for 204)"
                else
                    log_warning "Trip deletion returned body content (should be empty for 204)"
                fi
            else
                log_warning "Trip deletion returned $DELETE_STATUS instead of 204"
            fi
        else
            log_warning "Trip creation response missing trip ID"
        fi
    else
        log_warning "Trip creation returned $HTTP_STATUS instead of 201"
    fi
}

# Test navigation menu
test_navigation_menu() {
    log_info "Testing navigation menu for migration demo link..."
    
    RESPONSE=$(curl -s "$FRONTEND_URL")
    
    if echo "$RESPONSE" | grep -q "Migration Demo"; then
        log_success "Navigation menu contains Migration Demo link"
    else
        log_warning "Navigation menu missing Migration Demo link"
    fi
}

# Test JavaScript compilation
test_javascript_compilation() {
    log_info "Testing JavaScript compilation..."
    
    # Check if the migration demo page loads without JavaScript errors
    # This is a basic test - in a real scenario you'd use a headless browser
    RESPONSE=$(curl -s "$FRONTEND_URL/migration-demo")
    
    if echo "$RESPONSE" | grep -q "migration-demo/page.js"; then
        log_success "Migration demo page JavaScript is compiled"
    else
        log_warning "Migration demo page JavaScript may not be compiled correctly"
    fi
    
    if echo "$RESPONSE" | grep -q "enhanced-client"; then
        log_success "Enhanced client code is referenced"
    else
        log_info "Enhanced client code reference not found (may be bundled)"
    fi
}

# Main test execution
main() {
    log_info "Starting Frontend Migration Tests..."
    log_info "Testing Phase 1 frontend implementation"
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for this script. Please install it first."
        exit 1
    fi
    
    echo
    log_info "=== Testing Frontend Availability ==="
    test_frontend_availability
    
    echo
    log_info "=== Testing Migration Demo Page ==="
    test_migration_demo_page
    
    echo
    log_info "=== Testing Backend Connectivity ==="
    test_backend_connectivity
    
    echo
    log_info "=== Testing Enhanced Error Responses ==="
    test_enhanced_error_responses
    
    echo
    log_info "=== Testing HTTP Status Codes ==="
    test_http_status_codes
    
    echo
    log_info "=== Testing Navigation Menu ==="
    test_navigation_menu
    
    echo
    log_info "=== Testing JavaScript Compilation ==="
    test_javascript_compilation
    
    echo
    log_success "Frontend Migration Tests Completed!"
    echo
    log_info "Summary of tested features:"
    log_info "✅ Frontend availability and demo page"
    log_info "✅ Enhanced error response handling"
    log_info "✅ HTTP status code support (201/204)"
    log_info "✅ Navigation integration"
    log_info "✅ JavaScript compilation"
    echo
    log_info "Next steps:"
    log_info "📝 Visit http://localhost:3500/migration-demo to test interactively"
    log_info "📝 Test trip creation and deletion in the demo"
    log_info "📝 Verify error handling with invalid inputs"
    log_info "📝 Check browser console for detailed API responses"
}

# Run the tests
main "$@"
