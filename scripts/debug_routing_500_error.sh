#!/bin/bash

# Debug Routing 500 Error Script
# Comprehensive debugging for persistent routing 500 errors

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

# Test 1: Check Backend Health and Configuration
test_backend_health() {
    log_phase "Testing Backend Health and Configuration"
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✅ Backend is running"
        
        # Get health details
        HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
        echo "$HEALTH_RESPONSE" | grep -o '"routing_mode":"[^"]*"' | cut -d: -f2 | tr -d '"' | while read mode; do
            if [ "$mode" = "selfhost" ]; then
                log_success "✅ Routing mode: selfhost"
            else
                log_warning "⚠️ Routing mode: $mode"
            fi
        done
    else
        log_error "❌ Backend not accessible on localhost:8000"
        log_error "Please start the backend server"
        return 1
    fi
}

# Test 2: Check GraphHopper Service
test_graphhopper_service() {
    log_phase "Testing GraphHopper Service"
    
    if curl -s http://localhost:8989/health > /dev/null 2>&1; then
        log_success "✅ GraphHopper service is running"
        
        # Test route computation
        ROUTE_TEST=$(curl -s "http://localhost:8989/route?point=32.0853,34.7818&point=32.0944,34.7806&profile=car" 2>/dev/null)
        if echo "$ROUTE_TEST" | grep -q '"distance"'; then
            log_success "✅ GraphHopper can compute routes"
        else
            log_error "❌ GraphHopper route computation failed"
        fi
    else
        log_error "❌ GraphHopper service not accessible"
        log_error "Please start GraphHopper service"
        return 1
    fi
}

# Test 3: Test Direct API Call (No Auth)
test_direct_api_call() {
    log_phase "Testing Direct API Call (No Authentication)"
    
    DAY_ID="01K4J0CYB3YSGWDZB9N92V3ZQ4"
    
    log_info "Testing route computation for day: $DAY_ID"
    
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "http://localhost:8000/routing/days/$DAY_ID/route/compute" \
        -H "Content-Type: application/json" \
        -d '{"profile": "car", "optimize": true}' 2>/dev/null)
    
    HTTP_CODE="${RESPONSE: -3}"
    BODY="${RESPONSE%???}"
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "✅ Direct API call successful (200)"
        echo "$BODY" | grep -o '"distance":[0-9.]*' | head -1 | while read dist; do
            log_info "Route distance: $(echo $dist | cut -d: -f2)m"
        done
    else
        log_error "❌ Direct API call failed ($HTTP_CODE)"
        echo "$BODY" | head -5
    fi
}

# Test 4: Test Authenticated API Call
test_authenticated_api_call() {
    log_phase "Testing Authenticated API Call"
    
    DAY_ID="01K4J0CYB3YSGWDZB9N92V3ZQ4"
    
    log_info "Testing authenticated route computation for day: $DAY_ID"
    
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "http://localhost:8000/routing/days/$DAY_ID/route/compute" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-token" \
        -d '{"profile": "car", "optimize": true, "fixed_stop_ids": null, "options": {}}' 2>/dev/null)
    
    HTTP_CODE="${RESPONSE: -3}"
    BODY="${RESPONSE%???}"
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "✅ Authenticated API call successful (200)"
        echo "$BODY" | grep -o '"distance":[0-9.]*' | head -1 | while read dist; do
            log_info "Route distance: $(echo $dist | cut -d: -f2)m"
        done
    else
        log_error "❌ Authenticated API call failed ($HTTP_CODE)"
        echo "$BODY" | head -5
    fi
}

# Test 5: Check Day and Stops Data
test_day_and_stops() {
    log_phase "Testing Day and Stops Data"
    
    DAY_ID="01K4J0CYB3YSGWDZB9N92V3ZQ4"
    
    # Test day endpoint
    DAY_RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:8000/days/$DAY_ID" 2>/dev/null)
    DAY_HTTP_CODE="${DAY_RESPONSE: -3}"
    
    if [ "$DAY_HTTP_CODE" = "200" ]; then
        log_success "✅ Day exists and is accessible"
    else
        log_error "❌ Day not found or not accessible ($DAY_HTTP_CODE)"
        return 1
    fi
    
    # Test stops endpoint
    STOPS_RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:8000/days/$DAY_ID/stops" 2>/dev/null)
    STOPS_HTTP_CODE="${STOPS_RESPONSE: -3}"
    STOPS_BODY="${STOPS_RESPONSE%???}"
    
    if [ "$STOPS_HTTP_CODE" = "200" ]; then
        STOP_COUNT=$(echo "$STOPS_BODY" | grep -o '"id":"[^"]*"' | wc -l)
        log_success "✅ Day has $STOP_COUNT stops"
        
        if [ "$STOP_COUNT" -ge 2 ]; then
            log_success "✅ Sufficient stops for routing (need ≥2)"
        else
            log_warning "⚠️ Insufficient stops for routing (need ≥2, have $STOP_COUNT)"
        fi
    else
        log_error "❌ Cannot access stops for day ($STOPS_HTTP_CODE)"
    fi
}

# Test 6: Check Configuration
test_configuration() {
    log_phase "Testing Configuration"
    
    if [ -f ".env" ]; then
        log_success "✅ .env file exists"
        
        # Check GraphHopper URL
        GRAPHHOPPER_URL=$(grep "GRAPHHOPPER_BASE_URL=" .env | cut -d= -f2)
        if [ "$GRAPHHOPPER_URL" = "http://localhost:8989" ]; then
            log_success "✅ GraphHopper URL configured for localhost"
        elif [ "$GRAPHHOPPER_URL" = "http://graphhopper:8989" ]; then
            log_error "❌ GraphHopper URL still using Docker hostname"
            log_error "   Backend needs restart to pick up new configuration"
        else
            log_warning "⚠️ Unexpected GraphHopper URL: $GRAPHHOPPER_URL"
        fi
        
        # Check GraphHopper mode
        GRAPHHOPPER_MODE=$(grep "GRAPHHOPPER_MODE=" .env | cut -d= -f2)
        if [ "$GRAPHHOPPER_MODE" = "selfhost" ]; then
            log_success "✅ GraphHopper mode: selfhost"
        else
            log_warning "⚠️ GraphHopper mode: $GRAPHHOPPER_MODE"
        fi
    else
        log_error "❌ .env file not found"
    fi
}

# Main execution
main() {
    log_info "🔧 Starting Routing 500 Error Debug Suite"
    log_info "Comprehensive debugging for persistent routing errors"
    echo
    
    test_backend_health
    echo
    test_graphhopper_service
    echo
    test_configuration
    echo
    test_day_and_stops
    echo
    test_direct_api_call
    echo
    test_authenticated_api_call
    
    echo
    log_success "🎉 Routing Debug Suite Finished!"
    echo
    log_info "📊 Summary:"
    log_info "If direct API calls work but frontend calls fail:"
    log_info "1. Backend server needs restart to pick up new .env configuration"
    log_info "2. Authentication might be causing issues"
    log_info "3. Frontend might be sending malformed requests"
    echo
    log_info "🔄 To fix:"
    log_info "1. Stop backend server (Ctrl+C)"
    log_info "2. Restart: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    log_info "3. Check startup logs for GraphHopper URL"
    echo
    log_info "✅ If all tests pass, the issue is likely frontend-specific"
}

main "$@"
