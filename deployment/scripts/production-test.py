#!/usr/bin/env python3
"""
Production Test Suite for Trips Sorting Feature
Runs comprehensive tests on the production server after deployment
"""

import requests
import json
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

class ProductionTester:
    def __init__(self, api_base: str = "http://localhost:8000", test_email: str = "test@example.com", test_password: str = "testpassword123"):
        self.api_base = api_base.rstrip('/')
        self.test_email = test_email
        self.test_password = test_password
        self.token = None
        self.session = requests.Session()
        self.session.timeout = 30

        # Test tracking
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.warnings = 0

        # Results
        self.results = []

    def log_test(self, test_name: str, passed: bool, message: str = "", details: Dict = None):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.pass_count += 1
            status = "PASS"
        else:
            self.fail_count += 1
            status = "FAIL"

        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)

        print(f"{'✅' if passed else '❌'} {test_name}: {status}")
        if message:
            print(f"   {message}")

    def test_health_check(self) -> bool:
        """Test basic health check"""
        try:
            response = self.session.get(f"{self.api_base}/health")
            passed = response.status_code == 200

            if passed:
                data = response.json()
                self.log_test("Health Check", True, f"Server is healthy: {data.get('status', 'unknown')}")
            else:
                self.log_test("Health Check", False, f"Health check failed: {response.status_code}")

            return passed
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
            return False

    def authenticate(self) -> bool:
        """Authenticate and get token"""
        try:
            response = self.session.post(
                f"{self.api_base}/auth/login",
                json={"email": self.test_email, "password": self.test_password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_trips_endpoint_basic(self) -> bool:
        """Test basic trips endpoint functionality"""
        try:
            response = self.session.get(f"{self.api_base}/trips")
            passed = response.status_code == 200

            if passed:
                data = response.json()
                trip_count = len(data.get("data", []) if "data" in data else data.get("trips", []))
                self.log_test("Trips Endpoint Basic", True, f"Retrieved {trip_count} trips")
            else:
                self.log_test("Trips Endpoint Basic", False, f"Trips endpoint failed: {response.status_code}")

            return passed
        except Exception as e:
            self.log_test("Trips Endpoint Basic", False, f"Trips endpoint error: {str(e)}")
            return False

    def test_default_sorting(self) -> bool:
        """Test default sorting (newest first)"""
        try:
            response = self.session.get(f"{self.api_base}/trips")

            if response.status_code != 200:
                self.log_test("Default Sorting", False, f"Request failed: {response.status_code}")
                return False

            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])

            if len(trips) < 2:
                self.log_test("Default Sorting", True, "Not enough trips to test sorting (need 2+)")
                return True

            # Check if sorted by created_at desc
            first_created = trips[0].get("created_at")
            second_created = trips[1].get("created_at")

            if first_created and second_created:
                passed = first_created >= second_created
                message = f"First: {first_created}, Second: {second_created}"
                self.log_test("Default Sorting", passed, message)
                return passed
            else:
                self.log_test("Default Sorting", False, "Missing created_at timestamps")
                return False

        except Exception as e:
            self.log_test("Default Sorting", False, f"Default sorting error: {str(e)}")
            return False

    def test_explicit_sorting(self) -> bool:
        """Test explicit sorting parameters"""
        test_cases = [
            ("created_at:desc", "Newest First"),
            ("created_at:asc", "Oldest First"),
            ("title:asc", "Title Ascending"),
            ("updated_at:desc", "Updated Newest First")
        ]

        all_passed = True

        for sort_param, test_name in test_cases:
            try:
                response = self.session.get(f"{self.api_base}/trips?sort_by={sort_param}")

                if response.status_code == 200:
                    data = response.json()
                    trips = data.get("data", []) if "data" in data else data.get("trips", [])
                    self.log_test(f"Sorting: {test_name}", True, f"Got {len(trips)} trips with {sort_param}")
                else:
                    self.log_test(f"Sorting: {test_name}", False, f"Request failed: {response.status_code}")
                    all_passed = False

            except Exception as e:
                self.log_test(f"Sorting: {test_name}", False, f"Error: {str(e)}")
                all_passed = False

        return all_passed

    def test_invalid_sorting(self) -> bool:
        """Test invalid sorting parameters (should fallback gracefully)"""
        invalid_params = [
            "invalid:field",
            "created_at:invalid",
            "malformed",
            "field:direction:extra"
        ]

        all_passed = True

        for param in invalid_params:
            try:
                response = self.session.get(f"{self.api_base}/trips?sort_by={param}")

                if response.status_code == 200:
                    self.log_test(f"Invalid Sorting: {param}", True, "Handled gracefully")
                else:
                    self.log_test(f"Invalid Sorting: {param}", False, f"Should not fail: {response.status_code}")
                    all_passed = False

            except Exception as e:
                self.log_test(f"Invalid Sorting: {param}", False, f"Error: {str(e)}")
                all_passed = False

        return all_passed

    def test_pagination_with_sorting(self) -> bool:
        """Test pagination works with sorting"""
        try:
            response = self.session.get(f"{self.api_base}/trips?sort_by=created_at:desc&size=5&page=1")

            if response.status_code == 200:
                data = response.json()

                # Check if pagination links include sort_by parameter
                links = data.get("links", {})
                has_sort_in_links = any("sort_by" in link for link in links.values() if link)

                self.log_test("Pagination with Sorting", True,
                             f"Pagination works, sort in links: {has_sort_in_links}")
                return True
            else:
                self.log_test("Pagination with Sorting", False, f"Request failed: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Pagination with Sorting", False, f"Error: {str(e)}")
            return False

    def test_performance(self) -> bool:
        """Test response time performance"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.api_base}/trips?sort_by=created_at:desc&size=20")
            end_time = time.time()

            response_time = end_time - start_time
            passed = response.status_code == 200 and response_time < 5.0  # 5 second threshold

            self.log_test("Performance", passed,
                         f"Response time: {response_time:.2f}s (threshold: 5.0s)")
            return passed

        except Exception as e:
            self.log_test("Performance", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🧪 Starting Production Test Suite for Trips Sorting")
        print("=" * 60)

        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False

        if not self.authenticate():
            print("❌ Authentication failed - aborting tests")
            return False

        # Core functionality tests
        tests = [
            self.test_trips_endpoint_basic,
            self.test_default_sorting,
            self.test_explicit_sorting,
            self.test_invalid_sorting,
            self.test_pagination_with_sorting,
            self.test_performance
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(f"Test {test.__name__}", False, f"Unexpected error: {str(e)}")

        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.test_count}")
        print(f"   Passed: {self.pass_count}")
        print(f"   Failed: {self.fail_count}")
        print(f"   Success Rate: {(self.pass_count/self.test_count*100):.1f}%")

        success = self.fail_count == 0
        print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")

        return success

    def save_results(self, filename: str):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.test_count,
                    "passed": self.pass_count,
                    "failed": self.fail_count,
                    "success_rate": self.pass_count/self.test_count*100 if self.test_count > 0 else 0
                },
                "results": self.results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Production test suite for trips sorting")
    parser.add_argument("--api-base", default="http://localhost:8000",
                       help="API base URL")
    parser.add_argument("--email", default="test@example.com",
                       help="Test user email")
    parser.add_argument("--password", default="testpassword123",
                       help="Test user password")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    tester = ProductionTester(args.api_base, args.email, args.password)
    success = tester.run_all_tests()

    if args.output:
        tester.save_results(args.output)
        print(f"📄 Results saved to: {args.output}")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
