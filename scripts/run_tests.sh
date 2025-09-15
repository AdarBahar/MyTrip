#!/bin/bash

# Comprehensive test runner script for JWT authentication migration
# This script runs all tests and provides detailed feedback for each change

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run tests with error handling
run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    local description="$3"
    
    print_status "Running $test_name: $description"
    
    if eval "$test_command"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Function to check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend service is running"
    else
        print_warning "Backend service is not running. Starting with docker-compose..."
        docker-compose up -d backend
        sleep 10
    fi
    
    # Check frontend
    if curl -s http://localhost:3500 > /dev/null 2>&1; then
        print_success "Frontend service is running"
    else
        print_warning "Frontend service is not running. Starting with docker-compose..."
        docker-compose up -d frontend
        sleep 15
    fi
}

# Function to run backend tests
run_backend_tests() {
    print_status "=== BACKEND TESTS ==="
    
    cd backend
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    pip install -r requirements-test.txt 2>/dev/null || pip install pytest pytest-cov pytest-asyncio httpx
    
    local backend_failed=0
    
    # Unit tests
    run_test_suite "Backend Unit Tests" \
        "pytest tests/ -m 'unit' --tb=short" \
        "Testing individual components and functions" || backend_failed=1
    
    # Authentication tests (current implementation)
    run_test_suite "Authentication Tests (Current)" \
        "pytest tests/test_auth_comprehensive.py -m 'auth and not jwt' --tb=short" \
        "Testing current fake token authentication" || backend_failed=1
    
    # Security tests
    run_test_suite "Security Tests" \
        "pytest tests/ -m 'security' --tb=short" \
        "Testing security aspects and vulnerabilities" || backend_failed=1
    
    # API tests
    run_test_suite "API Tests" \
        "pytest tests/ -m 'api' --tb=short" \
        "Testing API endpoints and responses" || backend_failed=1
    
    # Performance tests
    run_test_suite "Performance Tests" \
        "pytest tests/ -m 'performance' --tb=short" \
        "Testing response times and performance" || backend_failed=1
    
    # Regression tests
    run_test_suite "Regression Tests" \
        "pytest tests/ -m 'regression' --tb=short" \
        "Testing that existing functionality still works" || backend_failed=1
    
    # Integration tests
    run_test_suite "Integration Tests" \
        "pytest tests/ -m 'integration' --tb=short" \
        "Testing component interactions" || backend_failed=1
    
    # Coverage report
    print_status "Generating coverage report..."
    pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --tb=short
    
    cd ..
    
    if [ $backend_failed -eq 0 ]; then
        print_success "All backend tests passed"
    else
        print_error "Some backend tests failed"
        return 1
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "=== FRONTEND TESTS ==="
    
    cd frontend
    
    local frontend_failed=0
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    npm install --silent
    
    # Unit tests
    run_test_suite "Frontend Unit Tests" \
        "npm run test -- --testPathPattern='.*\\.test\\.(ts|tsx)$' --testNamePattern='unit|Unit'" \
        "Testing React components and utilities" || frontend_failed=1
    
    # Authentication tests
    run_test_suite "Frontend Auth Tests" \
        "npm run test -- tests/lib/auth.test.tsx" \
        "Testing authentication context and hooks" || frontend_failed=1
    
    # Integration tests
    run_test_suite "Frontend Integration Tests" \
        "npm run test -- tests/integration/" \
        "Testing component interactions and workflows" || frontend_failed=1
    
    # Type checking
    run_test_suite "TypeScript Type Check" \
        "npm run type-check" \
        "Checking TypeScript types and interfaces" || frontend_failed=1
    
    # Linting
    run_test_suite "ESLint Check" \
        "npm run lint" \
        "Checking code style and potential issues" || frontend_failed=1
    
    cd ..
    
    if [ $frontend_failed -eq 0 ]; then
        print_success "All frontend tests passed"
    else
        print_error "Some frontend tests failed"
        return 1
    fi
}

# Function to run end-to-end tests
run_e2e_tests() {
    print_status "=== END-TO-END TESTS ==="
    
    # Check if services are running
    check_services
    
    cd backend
    
    # Run E2E tests
    run_test_suite "End-to-End Tests" \
        "pytest tests/ -m 'e2e' --tb=short" \
        "Testing complete user workflows"
    
    cd ..
}

# Function to run smoke tests
run_smoke_tests() {
    print_status "=== SMOKE TESTS ==="
    
    check_services
    
    local smoke_failed=0
    
    # Test basic endpoints
    run_test_suite "Health Check" \
        "curl -f http://localhost:8000/health" \
        "Testing backend health endpoint" || smoke_failed=1
    
    run_test_suite "Frontend Loading" \
        "curl -f http://localhost:3500" \
        "Testing frontend loads successfully" || smoke_failed=1
    
    # Test authentication endpoints
    run_test_suite "Auth Endpoints" \
        "curl -f http://localhost:8000/trips/ -H 'Authorization: Bearer fake_token_test'" \
        "Testing authentication is working" || smoke_failed=1
    
    if [ $smoke_failed -eq 0 ]; then
        print_success "All smoke tests passed"
    else
        print_error "Some smoke tests failed"
        return 1
    fi
}

# Function to generate test report
generate_report() {
    print_status "=== GENERATING TEST REPORT ==="
    
    local report_file="test_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Test Report - $(date)

## Test Summary

### Backend Tests
- Unit Tests: $(grep -c "test_" backend/tests/test_*.py 2>/dev/null || echo "N/A") tests
- Authentication Tests: $(grep -c "def test_" backend/tests/test_auth_comprehensive.py 2>/dev/null || echo "N/A") tests
- Security Tests: $(grep -c "@pytest.mark.security" backend/tests/*.py 2>/dev/null || echo "N/A") tests

### Frontend Tests
- Component Tests: $(find frontend/tests -name "*.test.tsx" | wc -l) test files
- Authentication Tests: 1 comprehensive test suite
- Integration Tests: $(find frontend/tests/integration -name "*.test.tsx" | wc -l) test files

### Coverage
- Backend Coverage: See htmlcov/index.html
- Frontend Coverage: See frontend/coverage/

### Test Results
$(if [ -f backend/htmlcov/index.html ]; then echo "✅ Backend coverage report generated"; else echo "❌ Backend coverage report missing"; fi)
$(if [ -f frontend/coverage/index.html ]; then echo "✅ Frontend coverage report generated"; else echo "❌ Frontend coverage report missing"; fi)

### Recommendations
1. Run tests before each commit
2. Maintain >80% code coverage
3. Add tests for new features
4. Update tests when changing authentication

EOF

    print_success "Test report generated: $report_file"
}

# Main execution
main() {
    print_status "Starting comprehensive test suite for JWT authentication migration"
    print_status "This will help identify issues after each authentication change"
    
    local overall_failed=0
    
    # Parse command line arguments
    case "${1:-all}" in
        "smoke")
            run_smoke_tests || overall_failed=1
            ;;
        "backend")
            run_backend_tests || overall_failed=1
            ;;
        "frontend")
            run_frontend_tests || overall_failed=1
            ;;
        "e2e")
            run_e2e_tests || overall_failed=1
            ;;
        "all")
            run_smoke_tests || overall_failed=1
            run_backend_tests || overall_failed=1
            run_frontend_tests || overall_failed=1
            run_e2e_tests || overall_failed=1
            ;;
        *)
            print_error "Usage: $0 [smoke|backend|frontend|e2e|all]"
            exit 1
            ;;
    esac
    
    generate_report
    
    if [ $overall_failed -eq 0 ]; then
        print_success "🎉 All tests passed! Ready for authentication changes."
    else
        print_error "❌ Some tests failed. Fix issues before proceeding with authentication changes."
        exit 1
    fi
}

# Run main function
main "$@"
