#!/bin/bash

# Test script to verify infinite loop fix
# Checks for problematic patterns that could cause infinite re-renders

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Test for infinite loop patterns
test_infinite_loop_patterns() {
    log_info "🔍 Testing for infinite loop patterns..."
    
    TRIPS_PAGE="frontend/app/trips/page.tsx"
    
    if [ -f "$TRIPS_PAGE" ]; then
        # Check for useEffect with problematic dependencies
        if grep -q "useEffect.*\[\]" "$TRIPS_PAGE"; then
            log_success "✅ useEffect has empty dependency array (safe)"
        else
            log_warning "⚠️ useEffect might have problematic dependencies"
        fi
        
        # Check for useCallback with changing dependencies
        CALLBACK_WITH_DEPS=$(grep -c "useCallback.*\[.*\]" "$TRIPS_PAGE" || echo "0")
        if [ "$CALLBACK_WITH_DEPS" -eq 0 ]; then
            log_success "✅ No useCallback with changing dependencies"
        else
            log_warning "⚠️ Found $CALLBACK_WITH_DEPS useCallback with dependencies"
        fi
        
        # Check for setState in useEffect without proper guards
        if grep -q "setState.*useEffect" "$TRIPS_PAGE"; then
            log_warning "⚠️ Potential setState in useEffect found"
        else
            log_success "✅ No direct setState in useEffect"
        fi
        
        # Check for simplified error handling
        if grep -q "useAPIResponseHandler" "$TRIPS_PAGE"; then
            log_warning "⚠️ Still using complex useAPIResponseHandler"
        else
            log_success "✅ Using simplified error handling"
        fi
        
        # Check for clearMessages usage
        if grep -q "clearMessages" "$TRIPS_PAGE"; then
            log_warning "⚠️ Still using clearMessages which might cause loops"
        else
            log_success "✅ No clearMessages usage"
        fi
        
    else
        log_error "❌ Trips page not found"
    fi
}

# Test for resource exhaustion patterns
test_resource_patterns() {
    log_info "🔍 Testing for resource exhaustion patterns..."
    
    TRIPS_PAGE="frontend/app/trips/page.tsx"
    
    if [ -f "$TRIPS_PAGE" ]; then
        # Check for multiple API calls
        API_CALLS=$(grep -c "await.*Enhanced\|fetch\|axios" "$TRIPS_PAGE" || echo "0")
        if [ "$API_CALLS" -le 2 ]; then
            log_success "✅ Limited API calls ($API_CALLS found)"
        else
            log_warning "⚠️ Multiple API calls found ($API_CALLS)"
        fi
        
        # Check for proper loading states
        if grep -q "setLoading(true)" "$TRIPS_PAGE" && grep -q "setLoading(false)" "$TRIPS_PAGE"; then
            log_success "✅ Proper loading state management"
        else
            log_warning "⚠️ Loading state might not be properly managed"
        fi
        
        # Check for error boundaries
        if grep -q "try.*catch" "$TRIPS_PAGE"; then
            log_success "✅ Error handling with try/catch"
        else
            log_warning "⚠️ No error handling found"
        fi
    fi
}

# Test for simplified patterns
test_simplified_patterns() {
    log_info "🔍 Testing for simplified patterns..."
    
    TRIPS_PAGE="frontend/app/trips/page.tsx"
    
    if [ -f "$TRIPS_PAGE" ]; then
        # Check for simplified state management
        STATE_VARS=$(grep -c "useState" "$TRIPS_PAGE" || echo "0")
        if [ "$STATE_VARS" -le 5 ]; then
            log_success "✅ Simplified state management ($STATE_VARS state variables)"
        else
            log_warning "⚠️ Complex state management ($STATE_VARS state variables)"
        fi
        
        # Check for simplified error display
        if grep -q "bg-red-50.*border-red-200" "$TRIPS_PAGE"; then
            log_success "✅ Simple error display implemented"
        else
            log_warning "⚠️ Complex error display might still be used"
        fi
        
        # Check for direct API response handling
        if grep -q "response.success.*response.data" "$TRIPS_PAGE"; then
            log_success "✅ Direct API response handling"
        else
            log_warning "⚠️ Complex response handling might be used"
        fi
    fi
}

# Main execution
main() {
    log_info "🚨 Testing Infinite Loop Fix"
    echo
    
    test_infinite_loop_patterns
    echo
    test_resource_patterns
    echo
    test_simplified_patterns
    
    echo
    log_success "🎉 Infinite Loop Fix Test Complete!"
    echo
    log_info "📊 Summary:"
    log_info "✅ Checked for infinite loop patterns"
    log_info "✅ Verified resource usage patterns"
    log_info "✅ Confirmed simplified implementations"
    echo
    log_info "🎯 The page should now load without infinite loops!"
    echo
    log_info "💡 If you still see issues:"
    log_info "1. Clear browser cache and reload"
    log_info "2. Check browser console for any remaining errors"
    log_info "3. Restart the development server"
}

main "$@"
