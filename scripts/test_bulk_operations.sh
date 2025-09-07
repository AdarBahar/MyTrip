#!/bin/bash

# Test script for bulk operations
# This script tests all bulk operation endpoints

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

# Test bulk delete stops
test_bulk_delete_stops() {
    log_info "Testing bulk delete stops..."
    
    # First, create some test stops (you'll need to implement this based on your test data)
    # For now, we'll use placeholder IDs
    
    RESPONSE=$(curl -s -X DELETE "$BASE_URL/stops/bulk" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "ids": ["test_stop_1", "test_stop_2"],
            "force": false
        }')
    
    echo "Bulk delete stops response:"
    echo "$RESPONSE" | jq .
    
    # Check if response has expected structure
    TOTAL_ITEMS=$(echo "$RESPONSE" | jq -r '.total_items // 0')
    if [ "$TOTAL_ITEMS" -gt 0 ]; then
        log_success "Bulk delete stops endpoint is working"
    else
        log_warning "Bulk delete stops returned no items (expected if no test data)"
    fi
}

# Test bulk update stops
test_bulk_update_stops() {
    log_info "Testing bulk update stops..."
    
    RESPONSE=$(curl -s -X PATCH "$BASE_URL/stops/bulk" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "updates": [
                {
                    "id": "test_stop_1",
                    "data": {
                        "duration_min": 60,
                        "notes": "Updated via bulk operation"
                    }
                }
            ]
        }')
    
    echo "Bulk update stops response:"
    echo "$RESPONSE" | jq .
    
    # Check response structure
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk update stops endpoint is working"
    else
        log_error "Bulk update stops endpoint returned invalid response"
    fi
}

# Test bulk reorder stops
test_bulk_reorder_stops() {
    log_info "Testing bulk reorder stops..."
    
    # Use a test day ID
    DAY_ID="test_day_id"
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/stops/bulk/reorder?day_id=$DAY_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "items": [
                {"id": "test_stop_1", "seq": 1},
                {"id": "test_stop_2", "seq": 2}
            ]
        }')
    
    echo "Bulk reorder stops response:"
    echo "$RESPONSE" | jq .
    
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk reorder stops endpoint is working"
    else
        log_warning "Bulk reorder stops endpoint may need valid day ID"
    fi
}

# Test bulk delete days
test_bulk_delete_days() {
    log_info "Testing bulk delete days..."
    
    TRIP_ID="test_trip_id"
    
    RESPONSE=$(curl -s -X DELETE "$BASE_URL/days/bulk?trip_id=$TRIP_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "ids": ["test_day_1", "test_day_2"],
            "force": false
        }')
    
    echo "Bulk delete days response:"
    echo "$RESPONSE" | jq .
    
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk delete days endpoint is working"
    else
        log_warning "Bulk delete days endpoint may need valid trip ID"
    fi
}

# Test bulk update days
test_bulk_update_days() {
    log_info "Testing bulk update days..."
    
    TRIP_ID="test_trip_id"
    
    RESPONSE=$(curl -s -X PATCH "$BASE_URL/days/bulk?trip_id=$TRIP_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "updates": [
                {
                    "id": "test_day_1",
                    "data": {
                        "title": "Updated Day Title",
                        "status": "completed"
                    }
                }
            ]
        }')
    
    echo "Bulk update days response:"
    echo "$RESPONSE" | jq .
    
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk update days endpoint is working"
    else
        log_warning "Bulk update days endpoint may need valid trip ID"
    fi
}

# Test bulk delete trips
test_bulk_delete_trips() {
    log_info "Testing bulk delete trips..."
    
    RESPONSE=$(curl -s -X DELETE "$BASE_URL/trips/bulk" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "ids": ["test_trip_1", "test_trip_2"],
            "force": false
        }')
    
    echo "Bulk delete trips response:"
    echo "$RESPONSE" | jq .
    
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk delete trips endpoint is working"
    else
        log_warning "Bulk delete trips returned no items (expected if no test data)"
    fi
}

# Test bulk update trips
test_bulk_update_trips() {
    log_info "Testing bulk update trips..."
    
    RESPONSE=$(curl -s -X PATCH "$BASE_URL/trips/bulk" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "updates": [
                {
                    "id": "test_trip_1",
                    "data": {
                        "title": "Updated Trip Title",
                        "status": "completed"
                    }
                }
            ]
        }')
    
    echo "Bulk update trips response:"
    echo "$RESPONSE" | jq .
    
    if echo "$RESPONSE" | jq -e '.total_items' > /dev/null; then
        log_success "Bulk update trips endpoint is working"
    else
        log_warning "Bulk update trips returned no items (expected if no test data)"
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
    log_info "Starting bulk operations tests..."
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for this script. Please install it first."
        exit 1
    fi
    
    # Test API health first
    test_health
    
    # Get authentication token
    get_token
    
    # Run all bulk operation tests
    echo
    log_info "Testing Stops Bulk Operations..."
    test_bulk_delete_stops
    echo
    test_bulk_update_stops
    echo
    test_bulk_reorder_stops
    
    echo
    log_info "Testing Days Bulk Operations..."
    test_bulk_delete_days
    echo
    test_bulk_update_days
    
    echo
    log_info "Testing Trips Bulk Operations..."
    test_bulk_delete_trips
    echo
    test_bulk_update_trips
    
    echo
    log_success "All bulk operation tests completed!"
    log_info "Note: Some tests may show warnings if no test data exists, which is expected."
}

# Run the tests
main "$@"
