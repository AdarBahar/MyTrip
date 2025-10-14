#!/usr/bin/env python3
"""
MyTrips API Comprehensive Test Suite
Run this from your local machine to test the backend API
Usage: python3 test_mytrips_api.py
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import argparse

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class APITester:
    def __init__(self, api_base: str = "https://mytrips-api.bahar.co.il", test_email: str = "test@example.com", test_password: str = None):
        self.api_base = api_base.rstrip('/')
        self.test_email = test_email
        self.test_password = test_password or self._get_default_password(test_email)
        self.token = None
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test tracking
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.warnings = 0
        
        # Test data storage
        self.trip_id = None
        self.day_id = None
        self.stop_id = None
        
        # Logging
        self.log_file = f"api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.responses = []

    def _get_default_password(self, email: str) -> str:
        """Get default password for known test users"""
        default_passwords = {
            "test@example.com": "password123",
            "adar.bahar@gmail.com": "admin123",
            "admin@mytrips.com": "admin123"
        }
        return default_passwords.get(email, "password123")
        
    def log(self, message: str, color: str = ""):
        """Log message to console and file"""
        colored_msg = f"{color}{message}{Colors.NC}" if color else message
        print(colored_msg)
        
        # Write to log file without color codes
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def test_start(self, name: str):
        """Start a new test"""
        self.test_count += 1
        self.log(f"[{self.test_count}] {name}", Colors.BLUE)
    
    def test_pass(self, message: str):
        """Mark test as passed"""
        self.pass_count += 1
        self.log(f"✅ PASS: {message}", Colors.GREEN)
    
    def test_fail(self, message: str, details: str = ""):
        """Mark test as failed"""
        self.fail_count += 1
        self.log(f"❌ FAIL: {message}", Colors.RED)
        if details:
            self.log(f"   Error: {details}")
    
    def test_warning(self, message: str):
        """Mark test as warning"""
        self.warnings += 1
        self.log(f"⚠️  WARNING: {message}", Colors.YELLOW)
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    auth: bool = True, expected_status: List[int] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.api_base}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers
            )
            
            # Store response for debugging
            self.responses.append({
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'url': url,
                'status_code': response.status_code,
                'response': response.text[:1000]  # Limit response size
            })
            
            result = {
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'data': None,
                'error': None
            }
            
            try:
                result['data'] = response.json()
            except:
                result['data'] = response.text
            
            if expected_status and response.status_code not in expected_status:
                result['success'] = False
                result['error'] = f"Expected status {expected_status}, got {response.status_code}"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def test_health(self):
        """Test health endpoint"""
        self.test_start("Health Check")
        
        result = self.make_request('GET', '/health', auth=False, expected_status=[200])
        
        if result['success']:
            self.test_pass("Health endpoint responding")
            self.log(f"   Response: {result['data']}")
        else:
            self.test_fail("Health endpoint failed", result['error'])
            return False
        return True
    
    def test_docs(self):
        """Test API documentation"""
        self.test_start("API Documentation")
        
        result = self.make_request('GET', '/docs', auth=False, expected_status=[200])
        
        if result['success']:
            self.test_pass("API docs accessible")
        else:
            self.test_fail("API docs not accessible", result['error'])
    
    def test_openapi(self):
        """Test OpenAPI specification"""
        self.test_start("OpenAPI Specification")
        
        result = self.make_request('GET', '/openapi.json', auth=False, expected_status=[200])
        
        if result['success'] and isinstance(result['data'], dict) and 'openapi' in result['data']:
            self.test_pass("OpenAPI spec available")
        else:
            self.test_fail("OpenAPI spec not available", result['error'])
    
    def test_authentication(self):
        """Test user authentication"""
        self.test_start("User Authentication")

        data = {"email": self.test_email, "password": self.test_password}
        result = self.make_request('POST', '/auth/login', data=data, auth=False, expected_status=[200])
        
        if result['success'] and result['data'] and 'access_token' in result['data']:
            self.token = result['data']['access_token']
            self.test_pass("Authentication successful")
            self.log(f"   Token: {self.token[:20]}...")
            return True
        else:
            self.test_fail("Authentication failed", result['error'])
            return False
    
    def test_protected_access(self):
        """Test protected endpoint access"""
        self.test_start("Protected Endpoint Access")
        
        if not self.token:
            self.test_fail("No authentication token available")
            return False
        
        result = self.make_request('GET', '/trips/', expected_status=[200])
        
        if result['success']:
            self.test_pass("Protected endpoint accessible with token")
            return True
        else:
            self.test_fail("Protected endpoint access failed", result['error'])
            return False
    
    def test_trip_crud(self):
        """Test trip CRUD operations"""
        self.test_start("Trip CRUD Operations")
        
        if not self.token:
            self.test_fail("No authentication token available")
            return False
        
        # Create trip
        trip_data = {
            "title": "API Test Trip",
            "destination": "Jerusalem, Israel"
        }
        
        result = self.make_request('POST', '/trips/', data=trip_data, expected_status=[200, 201])

        if result['success'] and result['data']:
            # Handle nested trip data structure
            trip_data_response = result['data'].get('trip', result['data'])
            if 'id' in trip_data_response:
                self.trip_id = trip_data_response['id']
                self.test_pass(f"Trip created successfully (ID: {self.trip_id})")
            else:
                self.test_fail("Trip creation failed - no ID in response", result['data'])
                return False
        else:
            self.test_fail("Trip creation failed", result['error'])
            return False
        
        # Read trip
        result = self.make_request('GET', f'/trips/{self.trip_id}', expected_status=[200])
        
        if result['success']:
            self.test_pass("Trip retrieved successfully")
        else:
            self.test_fail("Trip retrieval failed", result['error'])
        
        # Update trip
        update_data = {"title": "Updated API Test Trip"}
        result = self.make_request('PATCH', f'/trips/{self.trip_id}', data=update_data, expected_status=[200])
        
        if result['success']:
            self.test_pass("Trip updated successfully")
        else:
            self.test_warning(f"Trip update failed (Status: {result['status_code']}) - may not be implemented")
        
        return True
    
    def test_day_crud(self):
        """Test day CRUD operations"""
        self.test_start("Day CRUD Operations")
        
        if not self.token or not self.trip_id:
            self.test_fail("Missing token or trip ID")
            return False
        
        # Create day
        day_data = {
            "title": "Test Day 1",
            "date": "2024-12-01"
        }
        
        result = self.make_request('POST', f'/trips/{self.trip_id}/days/', data=day_data, expected_status=[200, 201])

        if result['success'] and result['data']:
            # Handle nested day data structure
            day_data_response = result['data'].get('day', result['data'])
            if 'id' in day_data_response:
                self.day_id = day_data_response['id']
                self.test_pass(f"Day created successfully (ID: {self.day_id})")
            else:
                self.test_fail("Day creation failed - no ID in response", result['data'])
                return False
        else:
            self.test_fail("Day creation failed", result['error'])
            return False
        
        # List days
        result = self.make_request('GET', f'/trips/{self.trip_id}/days/', expected_status=[200])
        
        if result['success']:
            self.test_pass("Days listed successfully")
        else:
            self.test_fail("Days listing failed", result['error'])
        
        return True
    
    def test_stop_crud(self):
        """Test stop CRUD operations"""
        self.test_start("Stop CRUD Operations")
        
        if not self.token or not self.day_id:
            self.test_fail("Missing token or day ID")
            return False
        
        # Create stop
        stop_data = {
            "day_id": self.day_id,
            "title": "Test Stop",
            "stop_type": "attraction"
        }
        
        result = self.make_request('POST', '/stops/', data=stop_data, expected_status=[200, 201])

        if result['success'] and result['data']:
            # Handle nested stop data structure
            stop_data_response = result['data'].get('stop', result['data'])
            if 'id' in stop_data_response:
                self.stop_id = stop_data_response['id']
                self.test_pass(f"Stop created successfully (ID: {self.stop_id})")
            else:
                self.test_fail("Stop creation failed - no ID in response", result['data'])
                return False
        else:
            self.test_fail("Stop creation failed", result['error'])
            return False
        
        # List stops
        result = self.make_request('GET', f'/stops/?day_id={self.day_id}', expected_status=[200])
        
        if result['success']:
            self.test_pass("Stops listed successfully")
        else:
            self.test_fail("Stops listing failed", result['error'])
        
        return True
    
    def test_places_search(self):
        """Test places search"""
        self.test_start("Places Search")
        
        if not self.token:
            self.test_fail("No authentication token available")
            return
        
        result = self.make_request('GET', '/places/search?query=Jerusalem', expected_status=[200])
        
        if result['success']:
            self.test_pass("Places search working")
        else:
            self.test_warning(f"Places search failed (Status: {result['status_code']}) - may require API keys")
    
    def test_user_settings(self):
        """Test user settings"""
        self.test_start("User Settings")
        
        if not self.token:
            self.test_fail("No authentication token available")
            return
        
        result = self.make_request('GET', '/settings/user', expected_status=[200])
        
        if result['success']:
            self.test_pass("User settings accessible")
        else:
            self.test_warning(f"User settings failed (Status: {result['status_code']})")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.test_start("Cleanup Test Data")
        
        if not self.token:
            self.test_warning("No token for cleanup")
            return
        
        # Delete trip (should cascade delete days and stops)
        if self.trip_id:
            result = self.make_request('DELETE', f'/trips/{self.trip_id}', expected_status=[200, 204])
            
            if result['success']:
                self.test_pass("Test trip deleted successfully")
            else:
                self.test_warning(f"Test trip deletion failed (Status: {result['status_code']})")
    
    def save_test_report(self):
        """Save detailed test report"""
        report = {
            'test_summary': {
                'total_tests': self.test_count,
                'passed': self.pass_count,
                'failed': self.fail_count,
                'warnings': self.warnings,
                'success_rate': round((self.pass_count / self.test_count) * 100, 2) if self.test_count > 0 else 0
            },
            'test_config': {
                'api_base': self.api_base,
                'test_email': self.test_email,
                'timestamp': datetime.now().isoformat()
            },
            'responses': self.responses
        }
        
        report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Detailed report saved to: {report_file}")
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 MyTrips API Comprehensive Test Suite", Colors.CYAN)
        self.log("=" * 50)
        self.log(f"API Base: {self.api_base}")
        self.log(f"Test Email: {self.test_email}")
        self.log(f"Test Password: {'*' * len(self.test_password)}")
        self.log(f"Log File: {self.log_file}")
        self.log(f"Started: {datetime.now().isoformat()}")
        self.log("")
        
        # Core functionality tests
        if not self.test_health():
            self.log("❌ Health check failed - aborting tests", Colors.RED)
            return False
        
        self.test_docs()
        self.test_openapi()
        
        if not self.test_authentication():
            self.log("❌ Authentication failed - aborting protected tests", Colors.RED)
            return False
        
        if not self.test_protected_access():
            self.log("❌ Protected access failed - aborting CRUD tests", Colors.RED)
            return False
        
        # CRUD operation tests
        self.test_trip_crud()
        self.test_day_crud()
        self.test_stop_crud()
        
        # Additional feature tests
        self.test_places_search()
        self.test_user_settings()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.log("")
        self.log("🎯 Test Summary", Colors.CYAN)
        self.log("=" * 20)
        self.log(f"Total Tests: {self.test_count}")
        self.log(f"Passed: {self.pass_count}", Colors.GREEN)
        self.log(f"Failed: {self.fail_count}", Colors.RED if self.fail_count > 0 else "")
        self.log(f"Warnings: {self.warnings}", Colors.YELLOW if self.warnings > 0 else "")
        
        if self.test_count > 0:
            success_rate = (self.pass_count / self.test_count) * 100
            self.log(f"Success Rate: {success_rate:.1f}%")
        
        self.log("")
        
        # Save detailed report
        self.save_test_report()
        
        if self.fail_count == 0:
            self.log("🎉 All critical tests passed!", Colors.GREEN)
            return True
        else:
            self.log("❌ Some tests failed. Check the log for details.", Colors.RED)
            return False

def main():
    parser = argparse.ArgumentParser(description='MyTrips API Test Suite')
    parser.add_argument('--api-base', default='https://mytrips-api.bahar.co.il',
                       help='API base URL')
    parser.add_argument('--email', default='test@example.com',
                       help='Test email for authentication')
    parser.add_argument('--password', default=None,
                       help='Test password for authentication (auto-detected if not provided)')

    args = parser.parse_args()

    tester = APITester(api_base=args.api_base, test_email=args.email, test_password=args.password)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
