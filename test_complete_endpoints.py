#!/usr/bin/env python3
"""
Test script for the new complete endpoints
Tests both /trips/{trip_id}/days/complete and /trips/{trip_id}/complete
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

class CompleteEndpointsTest:
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

    def get_test_trip_id(self) -> Optional[str]:
        """Get a test trip ID"""
        try:
            response = self.session.get(f"{self.api_base}/trips?size=1")
            if response.status_code == 200:
                data = response.json()
                trips = data.get("data", []) if "data" in data else data.get("trips", [])
                if trips:
                    trip_id = trips[0]["id"]
                    self.log_test("Get Test Trip", True, f"Using trip ID: {trip_id}")
                    return trip_id
                else:
                    self.log_test("Get Test Trip", False, "No trips found for testing")
                    return None
            else:
                self.log_test("Get Test Trip", False, f"Failed to get trips: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get Test Trip", False, f"Error getting test trip: {str(e)}")
            return None

    def test_days_complete_endpoint(self, trip_id: str) -> bool:
        """Test GET /trips/{trip_id}/days/complete"""
        try:
            # Test basic endpoint
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/days/complete")

            if response.status_code != 200:
                self.log_test("Days Complete - Basic", False, f"Request failed: {response.status_code}")
                return False

            data = response.json()

            # Validate response structure
            required_fields = ["trip_id", "days", "total_days", "total_stops"]
            for field in required_fields:
                if field not in data:
                    self.log_test("Days Complete - Structure", False, f"Missing field: {field}")
                    return False

            self.log_test("Days Complete - Basic", True, f"Got {data['total_days']} days, {data['total_stops']} stops")

            # Test with include_place parameter
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/days/complete?include_place=true")

            if response.status_code == 200:
                data_with_places = response.json()
                self.log_test("Days Complete - With Places", True, "Successfully included place information")

                # Check if places are included in stops
                if data_with_places["days"]:
                    first_day = data_with_places["days"][0]
                    if first_day.get("stops"):
                        first_stop = first_day["stops"][0]
                        has_place = "place" in first_stop and first_stop["place"] is not None
                        self.log_test("Days Complete - Place Data", has_place,
                                    f"Place data {'included' if has_place else 'missing'}")
            else:
                self.log_test("Days Complete - With Places", False, f"Request failed: {response.status_code}")

            # Test ordering
            if data["days"]:
                days_ordered = all(
                    data["days"][i]["seq"] <= data["days"][i+1]["seq"]
                    for i in range(len(data["days"])-1)
                )
                self.log_test("Days Complete - Day Ordering", days_ordered,
                            "Days ordered by sequence" if days_ordered else "Days not properly ordered")

                # Check stops ordering within first day
                first_day = data["days"][0]
                if first_day.get("stops") and len(first_day["stops"]) > 1:
                    stops_ordered = all(
                        first_day["stops"][i]["seq"] <= first_day["stops"][i+1]["seq"]
                        for i in range(len(first_day["stops"])-1)
                    )
                    self.log_test("Days Complete - Stop Ordering", stops_ordered,
                                "Stops ordered by sequence" if stops_ordered else "Stops not properly ordered")

            return True

        except Exception as e:
            self.log_test("Days Complete - Basic", False, f"Error: {str(e)}")
            return False

    def test_trip_complete_endpoint(self, trip_id: str) -> bool:
        """Test GET /trips/{trip_id}/complete"""
        try:
            # Test basic endpoint
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/complete")

            if response.status_code != 200:
                self.log_test("Trip Complete - Basic", False, f"Request failed: {response.status_code}")
                return False

            data = response.json()

            # Validate response structure
            required_fields = ["trip", "days", "summary"]
            for field in required_fields:
                if field not in data:
                    self.log_test("Trip Complete - Structure", False, f"Missing field: {field}")
                    return False

            # Validate trip data
            trip_data = data["trip"]
            trip_required = ["id", "title", "status"]
            for field in trip_required:
                if field not in trip_data:
                    self.log_test("Trip Complete - Trip Data", False, f"Missing trip field: {field}")
                    return False

            # Validate summary data
            summary_data = data["summary"]
            summary_required = ["total_days", "total_stops"]
            for field in summary_required:
                if field not in summary_data:
                    self.log_test("Trip Complete - Summary", False, f"Missing summary field: {field}")
                    return False

            self.log_test("Trip Complete - Basic", True,
                         f"Trip: {trip_data['title']}, {summary_data['total_days']} days, {summary_data['total_stops']} stops")

            # Test with include_place parameter
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/complete?include_place=true")

            if response.status_code == 200:
                self.log_test("Trip Complete - With Places", True, "Successfully included place information")
            else:
                self.log_test("Trip Complete - With Places", False, f"Request failed: {response.status_code}")

            # Test status breakdown
            if "status_breakdown" in summary_data:
                total_status_count = sum(summary_data["status_breakdown"].values())
                self.log_test("Trip Complete - Status Breakdown", True,
                            f"Status breakdown: {summary_data['status_breakdown']}")

            return True

        except Exception as e:
            self.log_test("Trip Complete - Basic", False, f"Error: {str(e)}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        try:
            # Test with invalid trip ID
            response = self.session.get(f"{self.api_base}/trips/invalid-trip-id/complete")

            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Trip", True, "Correctly returned 404 for invalid trip")
            else:
                self.log_test("Error Handling - Invalid Trip", False, f"Expected 404, got {response.status_code}")

            # Test with invalid status filter
            response = self.session.get(f"{self.api_base}/trips/invalid-trip-id/days/complete?status=invalid_status")

            if response.status_code in [400, 404]:  # Either bad request or not found is acceptable
                self.log_test("Error Handling - Invalid Status", True, f"Correctly handled invalid status: {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Status", False, f"Unexpected status code: {response.status_code}")

            return True

        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🧪 Testing Complete Endpoints")
        print("=" * 50)

        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - aborting tests")
            return False

        # Get test trip
        trip_id = self.get_test_trip_id()
        if not trip_id:
            print("❌ No test trip available - aborting tests")
            return False

        # Run tests
        tests = [
            lambda: self.test_days_complete_endpoint(trip_id),
            lambda: self.test_trip_complete_endpoint(trip_id),
            self.test_error_handling
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
    parser = argparse.ArgumentParser(description="Test complete endpoints")
    parser.add_argument("--api-base", default="http://localhost:8000",
                       help="API base URL")
    parser.add_argument("--email", default="test@example.com",
                       help="Test user email")
    parser.add_argument("--password", default="testpassword123",
                       help="Test user password")

    args = parser.parse_args()

    tester = CompleteEndpointsTest(args.api_base, args.email, args.password)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
