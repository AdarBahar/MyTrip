#!/bin/bash

# Test script for Phase 1 changes: HTTP Status Codes and Error Standardization
# This script validates the new status codes and error response formats

set -e

# Configuration
BASE_URL="http://localhost:8000"
EMAIL="test@example.com"

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

# Get authentication token
get_token() {
    log_info "Getting authentication token..."
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$EMAIL\"}" | jq -r '.access_token')
    
    if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
        log_error "Failed to get authentication token"
        exit 1
    fi
    
    log_success "Got authentication token: ${TOKEN:0:20}..."
}

# Test HTTP status codes for creation (should return 201)
test_creation_status_codes() {
    log_info "Testing creation status codes (expecting 201)..."
    
    # Test trip creation
    log_info "Testing trip creation..."
    RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/trips/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Test Trip for Status Code",
            "destination": "Test Destination"
        }')
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    echo "Trip creation response status: $HTTP_STATUS"
    echo "Response body:"
    echo "$BODY" | jq .
    
    if [ "$HTTP_STATUS" = "201" ]; then
        log_success "Trip creation returns correct 201 status"
        TRIP_ID=$(echo "$BODY" | jq -r '.trip.id')
        echo "Created trip ID: $TRIP_ID"
    else
        log_error "Trip creation returned $HTTP_STATUS instead of 201"
    fi
    
    # Test day creation (if trip was created)
    if [ ! -z "$TRIP_ID" ] && [ "$TRIP_ID" != "null" ]; then
        log_info "Testing day creation..."
        RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/trips/$TRIP_ID/days" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
                "title": "Test Day",
                "date": "2024-06-15"
            }')
        
        HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        BODY=$(echo "$RESPONSE" | sed 's/HTTPSTATUS:[0-9]*$//')
        
        echo "Day creation response status: $HTTP_STATUS"
        
        if [ "$HTTP_STATUS" = "201" ]; then
            log_success "Day creation returns correct 201 status"
            DAY_ID=$(echo "$BODY" | jq -r '.id')
        else
            log_error "Day creation returned $HTTP_STATUS instead of 201"
        fi
    fi
}

# Test HTTP status codes for deletion (should return 204)
test_deletion_status_codes() {
    log_info "Testing deletion status codes (expecting 204)..."
    
    # Test trip deletion (if we have a trip ID)
    if [ ! -z "$TRIP_ID" ] && [ "$TRIP_ID" != "null" ]; then
        log_info "Testing trip deletion..."
        RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE "$BASE_URL/trips/$TRIP_ID" \
            -H "Authorization: Bearer $TOKEN")
        
        HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        BODY=$(echo "$RESPONSE" | sed 's/HTTPSTATUS:[0-9]*$//')
        
        echo "Trip deletion response status: $HTTP_STATUS"
        echo "Response body: '$BODY'"
        
        if [ "$HTTP_STATUS" = "204" ]; then
            log_success "Trip deletion returns correct 204 status"
            if [ -z "$BODY" ] || [ "$BODY" = "" ]; then
                log_success "Trip deletion returns empty body (correct for 204)"
            else
                log_warning "Trip deletion returned body content (should be empty for 204)"
            fi
        else
            log_error "Trip deletion returned $HTTP_STATUS instead of 204"
        fi
    fi
}

# Test error response format
test_error_response_format() {
    log_info "Testing unified error response format..."
    
    # Test validation error (invalid trip data)
    log_info "Testing validation error format..."
    RESPONSE=$(curl -s -X POST "$BASE_URL/trips/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title": ""}')  # Empty title should cause validation error
    
    echo "Validation error response:"
    if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo "$RESPONSE" | jq .
    else
        echo "Raw response: $RESPONSE"
    fi
    
    # Check if response has new error format
    ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.error_code // empty')
    ERROR_MESSAGE=$(echo "$RESPONSE" | jq -r '.error.message // empty')
    TIMESTAMP=$(echo "$RESPONSE" | jq -r '.timestamp // empty')
    REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id // empty')
    
    if [ ! -z "$ERROR_CODE" ]; then
        log_success "Error response has error_code: $ERROR_CODE"
    else
        log_error "Error response missing error_code"
    fi
    
    if [ ! -z "$ERROR_MESSAGE" ]; then
        log_success "Error response has message: $ERROR_MESSAGE"
    else
        log_error "Error response missing message"
    fi
    
    if [ ! -z "$TIMESTAMP" ]; then
        log_success "Error response has timestamp: $TIMESTAMP"
    else
        log_warning "Error response missing timestamp"
    fi
    
    if [ ! -z "$REQUEST_ID" ]; then
        log_success "Error response has request_id: $REQUEST_ID"
    else
        log_warning "Error response missing request_id"
    fi
    
    # Test not found error
    log_info "Testing not found error format..."
    RESPONSE=$(curl -s -X GET "$BASE_URL/trips/nonexistent-trip-id" \
        -H "Authorization: Bearer $TOKEN")
    
    echo "Not found error response:"
    echo "$RESPONSE" | jq .
    
    ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.error_code // empty')
    if [ "$ERROR_CODE" = "RESOURCE_NOT_FOUND" ]; then
        log_success "Not found error has correct error_code: $ERROR_CODE"
    else
        log_warning "Not found error has unexpected error_code: $ERROR_CODE"
    fi
}

# Test authentication error
test_authentication_error() {
    log_info "Testing authentication error format..."
    
    # Make request without token
    RESPONSE=$(curl -s -X GET "$BASE_URL/trips/")
    
    echo "Authentication error response:"
    echo "$RESPONSE" | jq .
    
    ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.error_code // empty')
    if [ "$ERROR_CODE" = "AUTHENTICATION_REQUIRED" ]; then
        log_success "Authentication error has correct error_code: $ERROR_CODE"
    else
        log_warning "Authentication error has unexpected error_code: $ERROR_CODE"
    fi
    
    # Check for suggestions
    SUGGESTIONS=$(echo "$RESPONSE" | jq -r '.error.suggestions // empty')
    if [ ! -z "$SUGGESTIONS" ] && [ "$SUGGESTIONS" != "null" ]; then
        log_success "Authentication error includes helpful suggestions"
    else
        log_warning "Authentication error missing suggestions"
    fi
}

# Test API health
test_health() {
    log_info "Testing API health..."
    
    RESPONSE=$(curl -s "$BASE_URL/health")
    echo "Health check response:"
    echo "$RESPONSE" | jq .
    
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    if [ "$STATUS" = "healthy" ]; then
        log_success "API is healthy"
    else
        log_error "API health check failed"
        exit 1
    fi
}

# Main test execution
main() {
    log_info "Starting Phase 1 implementation tests..."
    log_info "Testing HTTP Status Codes and Error Standardization"
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for this script. Please install it first."
        exit 1
    fi
    
    # Test API health first
    test_health
    
    # Get authentication token
    get_token
    
    # Run status code tests
    echo
    log_info "=== Testing HTTP Status Codes ==="
    test_creation_status_codes
    echo
    test_deletion_status_codes
    
    # Run error format tests
    echo
    log_info "=== Testing Error Response Format ==="
    test_error_response_format
    echo
    test_authentication_error
    
    echo
    log_success "Phase 1 implementation tests completed!"
    echo
    log_info "Summary of expected changes:"
    log_info "✅ POST operations should return 201 Created"
    log_info "✅ DELETE operations should return 204 No Content"
    log_info "✅ Error responses should have structured format with error_code, message, timestamp"
    log_info "✅ Error responses should include actionable suggestions"
    log_info "✅ Request tracking with unique request_id"
    echo
    log_info "Frontend changes needed:"
    log_info "📝 Update success handling for 201/204 status codes"
    log_info "📝 Update error handling to use new error schema"
    log_info "📝 See docs/FRONTEND_MIGRATION_GUIDE.md for details"
}

# Run the tests
main "$@"
