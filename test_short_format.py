#!/usr/bin/env python3
"""
Test script for the new short format endpoint
Tests GET /trips?format=short
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any, Optional

class ShortFormatTest:
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

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.pass_count += 1
            status = "PASS"
            icon = "✅"
        else:
            self.fail_count += 1
            status = "FAIL"
            icon = "❌"

        print(f"{icon} {test_name}: {status}")
        if message:
            print(f"   {message}")

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

    def test_short_format_basic(self) -> bool:
        """Test basic short format endpoint"""
        try:
            response = self.session.get(f"{self.api_base}/trips?format=short&size=5")

            if response.status_code != 200:
                self.log_test("Short Format - Basic", False, f"Request failed: {response.status_code}")
                return False

            data = response.json()

            # Validate response structure
            required_fields = ["data", "meta", "links"]
            for field in required_fields:
                if field not in data:
                    self.log_test("Short Format - Structure", False, f"Missing field: {field}")
                    return False

            self.log_test("Short Format - Basic", True, f"Got {len(data['data'])} trips")

            # Validate trip structure if we have trips
            if data["data"]:
                trip = data["data"][0]
                trip_required = ["slug", "title", "destination", "start_date", "timezone", "status", "is_published", "created_by", "members", "total_days", "days"]

                for field in trip_required:
                    if field not in trip:
                        self.log_test("Short Format - Trip Structure", False, f"Missing trip field: {field}")
                        return False

                self.log_test("Short Format - Trip Structure", True, f"Trip: {trip['title']}, {trip['total_days']} days")

                # Validate days structure
                if isinstance(trip["days"], list):
                    self.log_test("Short Format - Days Type", True, "Days is a list")

                    if trip["days"]:
                        day = trip["days"][0]
                        day_required = ["day", "start", "stops", "end"]

                        for field in day_required:
                            if field not in day:
                                self.log_test("Short Format - Day Structure", False, f"Missing day field: {field}")
                                return False

                        self.log_test("Short Format - Day Structure", True,
                                    f"Day {day['day']}: start={day['start']}, stops={day['stops']}, end={day['end']}")
                else:
                    self.log_test("Short Format - Days Type", False, f"Days should be a list, got {type(trip['days'])}")

            return True

        except Exception as e:
            self.log_test("Short Format - Basic", False, f"Error: {str(e)}")
            return False

    def test_short_format_with_params(self) -> bool:
        """Test short format with various parameters"""
        try:
            # Test with pagination
            response = self.session.get(f"{self.api_base}/trips?format=short&page=1&size=2")

            if response.status_code == 200:
                data = response.json()
                self.log_test("Short Format - Pagination", True, f"Page 1, size 2: got {len(data['data'])} trips")
            else:
                self.log_test("Short Format - Pagination", False, f"Request failed: {response.status_code}")

            # Test with status filter
            response = self.session.get(f"{self.api_base}/trips?format=short&status=active")

            if response.status_code == 200:
                data = response.json()
                self.log_test("Short Format - Status Filter", True, f"Active trips: {len(data['data'])}")
            else:
                self.log_test("Short Format - Status Filter", False, f"Request failed: {response.status_code}")

            # Test with sorting
            response = self.session.get(f"{self.api_base}/trips?format=short&sort_by=title:asc")

            if response.status_code == 200:
                data = response.json()
                self.log_test("Short Format - Sorting", True, f"Sorted by title: {len(data['data'])} trips")
            else:
                self.log_test("Short Format - Sorting", False, f"Request failed: {response.status_code}")

            return True

        except Exception as e:
            self.log_test("Short Format - Parameters", False, f"Error: {str(e)}")
            return False

    def test_format_comparison(self) -> bool:
        """Compare short format with modern format"""
        try:
            # Get modern format
            response_modern = self.session.get(f"{self.api_base}/trips?format=modern&size=1")
            response_short = self.session.get(f"{self.api_base}/trips?format=short&size=1")

            if response_modern.status_code != 200 or response_short.status_code != 200:
                self.log_test("Format Comparison", False, "Failed to get both formats")
                return False

            modern_data = response_modern.json()
            short_data = response_short.json()

            # Both should have same meta structure
            if modern_data.get("meta") and short_data.get("meta"):
                self.log_test("Format Comparison - Meta", True, "Both formats have meta")
            else:
                self.log_test("Format Comparison - Meta", False, "Meta structure differs")

            # Short format should have days array, modern shouldn't
            if short_data["data"] and modern_data["data"]:
                short_trip = short_data["data"][0]
                modern_trip = modern_data["data"][0]

                has_short_days = "days" in short_trip and isinstance(short_trip["days"], list)
                has_modern_days = "days" in modern_trip

                if has_short_days and not has_modern_days:
                    self.log_test("Format Comparison - Days", True, "Short format has days, modern doesn't")
                else:
                    self.log_test("Format Comparison - Days", False, f"Short days: {has_short_days}, Modern days: {has_modern_days}")

            return True

        except Exception as e:
            self.log_test("Format Comparison", False, f"Error: {str(e)}")
            return False

    def test_response_sample(self) -> bool:
        """Print a sample response for verification"""
        try:
            response = self.session.get(f"{self.api_base}/trips?format=short&size=1")

            if response.status_code == 200:
                data = response.json()
                print("\n📋 Sample Short Format Response:")
                print("=" * 50)
                print(json.dumps(data, indent=2))
                print("=" * 50)
                self.log_test("Response Sample", True, "Sample response printed")
                return True
            else:
                self.log_test("Response Sample", False, f"Request failed: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Response Sample", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🧪 Testing Short Format Endpoint")
        print("=" * 50)

        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - aborting tests")
            return False

        # Run tests
        tests = [
            self.test_short_format_basic,
            self.test_short_format_with_params,
            self.test_format_comparison,
            self.test_response_sample
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(f"Test {test.__name__}", False, f"Unexpected error: {str(e)}")

        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.test_count}")
        print(f"   Passed: {self.pass_count}")
        print(f"   Failed: {self.fail_count}")
        print(f"   Success Rate: {(self.pass_count/self.test_count*100):.1f}%")

        success = self.fail_count == 0
        print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")

        return success

def main():
    parser = argparse.ArgumentParser(description="Test short format endpoint")
    parser.add_argument("--api-base", default="http://localhost:8000",
                       help="API base URL")
    parser.add_argument("--email", default="test@example.com",
                       help="Test user email")
    parser.add_argument("--password", default="testpassword123",
                       help="Test user password")

    args = parser.parse_args()

    tester = ShortFormatTest(args.api_base, args.email, args.password)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
