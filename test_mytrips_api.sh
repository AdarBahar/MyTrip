#!/bin/bash

# MyTrips API Comprehensive Test Script
# Run this from your local machine to test the backend API
# Usage: ./test_mytrips_api.sh

set -e

# Configuration
API_BASE="https://mytrips-api.bahar.co.il"
TEST_EMAIL="test@example.com"
LOG_FILE="api_test_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
TOKEN=""
TRIP_ID=""
DAY_ID=""
STOP_ID=""
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Test result functions
test_start() {
    TEST_COUNT=$((TEST_COUNT + 1))
    log "${BLUE}[$TEST_COUNT] $1${NC}"
}

test_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    log "${GREEN}✅ PASS: $1${NC}"
}

test_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    log "${RED}❌ FAIL: $1${NC}"
    if [ "$2" != "" ]; then
        log "   Error: $2"
    fi
}

test_warning() {
    log "${YELLOW}⚠️  WARNING: $1${NC}"
}

# HTTP request function with error handling
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local headers="$4"
    
    local url="$API_BASE$endpoint"
    local curl_cmd="curl -s -w '%{http_code}' -X $method '$url'"
    
    if [ "$headers" != "" ]; then
        curl_cmd="$curl_cmd $headers"
    fi
    
    if [ "$data" != "" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    # Execute request and capture response + status code
    local response=$(eval $curl_cmd)
    local status_code="${response: -3}"
    local body="${response%???}"
    
    echo "$status_code|$body"
}

# Parse JSON safely
parse_json() {
    local json="$1"
    local key="$2"
    echo "$json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$key', ''))" 2>/dev/null || echo ""
}

# Test functions
test_health() {
    test_start "Health Check"
    
    local result=$(api_request "GET" "/health")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "200" ]; then
        test_pass "Health endpoint responding"
        log "   Response: $body"
    else
        test_fail "Health endpoint failed" "Status: $status, Body: $body"
        return 1
    fi
}

test_docs() {
    test_start "API Documentation"
    
    local result=$(api_request "GET" "/docs")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "API docs accessible"
    else
        test_fail "API docs not accessible" "Status: $status"
    fi
}

test_openapi() {
    test_start "OpenAPI Specification"
    
    local result=$(api_request "GET" "/openapi.json")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "200" ] && [[ "$body" == *"openapi"* ]]; then
        test_pass "OpenAPI spec available"
    else
        test_fail "OpenAPI spec not available" "Status: $status"
    fi
}

test_authentication() {
    test_start "User Authentication"
    
    local data="{\"email\": \"$TEST_EMAIL\"}"
    local result=$(api_request "POST" "/auth/login" "$data")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "200" ]; then
        TOKEN=$(parse_json "$body" "access_token")
        if [ "$TOKEN" != "" ]; then
            test_pass "Authentication successful"
            log "   Token: ${TOKEN:0:20}..."
        else
            test_fail "No token in response" "$body"
            return 1
        fi
    else
        test_fail "Authentication failed" "Status: $status, Body: $body"
        return 1
    fi
}

test_protected_access() {
    test_start "Protected Endpoint Access"
    
    if [ "$TOKEN" = "" ]; then
        test_fail "No authentication token available"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    local result=$(api_request "GET" "/trips/" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "200" ]; then
        test_pass "Protected endpoint accessible with token"
    else
        test_fail "Protected endpoint access failed" "Status: $status, Body: $body"
        return 1
    fi
}

test_trip_crud() {
    test_start "Trip CRUD Operations"
    
    if [ "$TOKEN" = "" ]; then
        test_fail "No authentication token available"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    
    # Create trip
    local create_data='{"title": "API Test Trip", "destination": "Jerusalem, Israel"}'
    local result=$(api_request "POST" "/trips/" "$create_data" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "201" ] || [ "$status" = "200" ]; then
        TRIP_ID=$(parse_json "$body" "id")
        if [ "$TRIP_ID" != "" ]; then
            test_pass "Trip created successfully (ID: $TRIP_ID)"
        else
            test_fail "Trip created but no ID returned" "$body"
            return 1
        fi
    else
        test_fail "Trip creation failed" "Status: $status, Body: $body"
        return 1
    fi
    
    # Read trip
    local result=$(api_request "GET" "/trips/$TRIP_ID" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "Trip retrieved successfully"
    else
        test_fail "Trip retrieval failed" "Status: $status"
    fi
    
    # Update trip
    local update_data='{"title": "Updated API Test Trip"}'
    local result=$(api_request "PATCH" "/trips/$TRIP_ID" "$update_data" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "Trip updated successfully"
    else
        test_warning "Trip update failed (Status: $status) - may not be implemented"
    fi
}

test_day_crud() {
    test_start "Day CRUD Operations"
    
    if [ "$TOKEN" = "" ] || [ "$TRIP_ID" = "" ]; then
        test_fail "Missing token or trip ID"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    
    # Create day
    local create_data='{"title": "Test Day 1", "date": "2024-12-01"}'
    local result=$(api_request "POST" "/trips/$TRIP_ID/days/" "$create_data" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "201" ] || [ "$status" = "200" ]; then
        DAY_ID=$(parse_json "$body" "id")
        if [ "$DAY_ID" != "" ]; then
            test_pass "Day created successfully (ID: $DAY_ID)"
        else
            test_fail "Day created but no ID returned" "$body"
            return 1
        fi
    else
        test_fail "Day creation failed" "Status: $status, Body: $body"
        return 1
    fi
    
    # List days for trip
    local result=$(api_request "GET" "/trips/$TRIP_ID/days/" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "Days listed successfully"
    else
        test_fail "Days listing failed" "Status: $status"
    fi
}

test_stop_crud() {
    test_start "Stop CRUD Operations"
    
    if [ "$TOKEN" = "" ] || [ "$DAY_ID" = "" ]; then
        test_fail "Missing token or day ID"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    
    # Create stop
    local create_data="{\"day_id\": \"$DAY_ID\", \"title\": \"Test Stop\", \"stop_type\": \"attraction\"}"
    local result=$(api_request "POST" "/stops/" "$create_data" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "201" ] || [ "$status" = "200" ]; then
        STOP_ID=$(parse_json "$body" "id")
        if [ "$STOP_ID" != "" ]; then
            test_pass "Stop created successfully (ID: $STOP_ID)"
        else
            test_fail "Stop created but no ID returned" "$body"
            return 1
        fi
    else
        test_fail "Stop creation failed" "Status: $status, Body: $body"
        return 1
    fi
    
    # List stops
    local result=$(api_request "GET" "/stops/?day_id=$DAY_ID" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "Stops listed successfully"
    else
        test_fail "Stops listing failed" "Status: $status"
    fi
}

test_places_search() {
    test_start "Places Search"
    
    if [ "$TOKEN" = "" ]; then
        test_fail "No authentication token available"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    local result=$(api_request "GET" "/places/search?query=Jerusalem" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    local body=$(echo "$result" | cut -d'|' -f2)
    
    if [ "$status" = "200" ]; then
        test_pass "Places search working"
    else
        test_warning "Places search failed (Status: $status) - may require API keys"
    fi
}

test_user_settings() {
    test_start "User Settings"
    
    if [ "$TOKEN" = "" ]; then
        test_fail "No authentication token available"
        return 1
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    local result=$(api_request "GET" "/settings/user" "" "$headers")
    local status=$(echo "$result" | cut -d'|' -f1)
    
    if [ "$status" = "200" ]; then
        test_pass "User settings accessible"
    else
        test_warning "User settings failed (Status: $status)"
    fi
}

# Cleanup function
cleanup_test_data() {
    test_start "Cleanup Test Data"
    
    if [ "$TOKEN" = "" ]; then
        test_warning "No token for cleanup"
        return
    fi
    
    local headers="-H 'Authorization: Bearer $TOKEN'"
    
    # Delete trip (should cascade delete days and stops)
    if [ "$TRIP_ID" != "" ]; then
        local result=$(api_request "DELETE" "/trips/$TRIP_ID" "" "$headers")
        local status=$(echo "$result" | cut -d'|' -f1)
        
        if [ "$status" = "200" ] || [ "$status" = "204" ]; then
            test_pass "Test trip deleted successfully"
        else
            test_warning "Test trip deletion failed (Status: $status)"
        fi
    fi
}

# Main test execution
main() {
    log "🚀 MyTrips API Comprehensive Test Suite"
    log "========================================"
    log "API Base: $API_BASE"
    log "Test Email: $TEST_EMAIL"
    log "Log File: $LOG_FILE"
    log "Started: $(date)"
    log ""
    
    # Core functionality tests
    test_health || exit 1
    test_docs
    test_openapi
    test_authentication || exit 1
    test_protected_access || exit 1
    
    # CRUD operation tests
    test_trip_crud
    test_day_crud
    test_stop_crud
    
    # Additional feature tests
    test_places_search
    test_user_settings
    
    # Cleanup
    cleanup_test_data
    
    # Summary
    log ""
    log "🎯 Test Summary"
    log "==============="
    log "Total Tests: $TEST_COUNT"
    log "Passed: $PASS_COUNT"
    log "Failed: $FAIL_COUNT"
    log "Success Rate: $(( PASS_COUNT * 100 / TEST_COUNT ))%"
    log ""
    
    if [ $FAIL_COUNT -eq 0 ]; then
        log "${GREEN}🎉 All critical tests passed!${NC}"
        exit 0
    else
        log "${RED}❌ Some tests failed. Check the log for details.${NC}"
        exit 1
    fi
}

# Check dependencies
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

# Run tests
main "$@"
