#!/usr/bin/env python3
"""
Production Deployment Test Suite
Tests all new endpoints and formats to ensure they work correctly in production
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any, List, Optional

class ProductionTester:
    def __init__(self, api_base: str = "https://mytrips-api.bahar.co.il", token: Optional[str] = None):
        self.api_base = api_base.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
        
        # Test tracking
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def log_test(self, test_name: str, passed: bool, message: str = "", response_data: Any = None):
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
        if response_data and not passed:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")

    def test_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.api_base}/health")
            success = response.status_code == 200
            self.log_test("Health Endpoint", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {str(e)}")
            return False

    def test_swagger_docs(self) -> bool:
        """Test Swagger documentation includes new endpoints"""
        try:
            response = self.session.get(f"{self.api_base}/openapi.json")
            if response.status_code != 200:
                self.log_test("Swagger Documentation", False, 
                             f"Status: {response.status_code}")
                return False
            
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            # Check for complete endpoints
            complete_endpoints = [
                "/trips/{trip_id}/days/complete",
                "/trips/{trip_id}/complete"
            ]
            
            missing_endpoints = []
            for endpoint in complete_endpoints:
                if endpoint not in paths:
                    missing_endpoints.append(endpoint)
            
            # Check for short format in trips endpoint
            trips_endpoint = paths.get("/trips/", {})
            has_format_param = False
            if "get" in trips_endpoint:
                params = trips_endpoint["get"].get("parameters", [])
                for param in params:
                    if param.get("name") == "format":
                        has_format_param = True
                        break
            
            success = len(missing_endpoints) == 0 and has_format_param
            message = ""
            if missing_endpoints:
                message += f"Missing endpoints: {missing_endpoints}. "
            if not has_format_param:
                message += "Missing format parameter in /trips/. "
            
            self.log_test("Swagger Documentation", success, message)
            return success
            
        except Exception as e:
            self.log_test("Swagger Documentation", False, f"Error: {str(e)}")
            return False

    def test_trips_short_format(self, owner_id: str) -> bool:
        """Test trips endpoint with short format"""
        try:
            response = self.session.get(
                f"{self.api_base}/trips/",
                params={
                    "owner": owner_id,
                    "format": "short",
                    "size": 5
                }
            )
            
            if response.status_code != 200:
                self.log_test("Trips Short Format", False, 
                             f"Status: {response.status_code}", response.json())
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["data", "meta", "links"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Trips Short Format", False, 
                             f"Missing fields: {missing_fields}")
                return False
            
            # Validate trip data structure
            trips = data.get("data", [])
            if trips:
                trip = trips[0]
                required_trip_fields = ["slug", "title", "total_days", "days"]
                missing_trip_fields = [field for field in required_trip_fields if field not in trip]
                
                if missing_trip_fields:
                    self.log_test("Trips Short Format", False, 
                                 f"Missing trip fields: {missing_trip_fields}")
                    return False
                
                # Validate day structure
                days = trip.get("days", [])
                if days:
                    day = days[0]
                    required_day_fields = ["day", "start", "stops", "end"]
                    missing_day_fields = [field for field in required_day_fields if field not in day]
                    
                    if missing_day_fields:
                        self.log_test("Trips Short Format", False, 
                                     f"Missing day fields: {missing_day_fields}")
                        return False
            
            self.log_test("Trips Short Format", True, 
                         f"Found {len(trips)} trips with correct structure")
            return True
            
        except Exception as e:
            self.log_test("Trips Short Format", False, f"Error: {str(e)}")
            return False

    def test_trips_modern_format(self, owner_id: str) -> bool:
        """Test trips endpoint with modern format (baseline)"""
        try:
            response = self.session.get(
                f"{self.api_base}/trips/",
                params={
                    "owner": owner_id,
                    "format": "modern",
                    "size": 5
                }
            )
            
            success = response.status_code == 200
            self.log_test("Trips Modern Format", success, 
                         f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Trips Modern Format", False, f"Error: {str(e)}")
            return False

    def test_complete_endpoints(self, trip_id: str) -> bool:
        """Test complete endpoints if trip_id is available"""
        if not trip_id:
            self.log_test("Complete Endpoints", False, "No trip_id provided")
            return False
        
        success = True
        
        # Test days complete endpoint
        try:
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/days/complete")
            days_success = response.status_code == 200
            self.log_test("Days Complete Endpoint", days_success, 
                         f"Status: {response.status_code}")
            success = success and days_success
        except Exception as e:
            self.log_test("Days Complete Endpoint", False, f"Error: {str(e)}")
            success = False
        
        # Test trip complete endpoint
        try:
            response = self.session.get(f"{self.api_base}/trips/{trip_id}/complete")
            trip_success = response.status_code == 200
            self.log_test("Trip Complete Endpoint", trip_success, 
                         f"Status: {response.status_code}")
            success = success and trip_success
        except Exception as e:
            self.log_test("Trip Complete Endpoint", False, f"Error: {str(e)}")
            success = False
        
        return success

    def run_full_test_suite(self, owner_id: str, trip_id: Optional[str] = None) -> bool:
        """Run complete test suite"""
        print("🧪 Production Deployment Test Suite")
        print("=" * 50)
        print(f"API Base: {self.api_base}")
        print(f"Owner ID: {owner_id}")
        print(f"Trip ID: {trip_id or 'Not provided'}")
        print("")
        
        # Run all tests
        self.test_health_endpoint()
        self.test_swagger_docs()
        self.test_trips_modern_format(owner_id)
        self.test_trips_short_format(owner_id)
        
        if trip_id:
            self.test_complete_endpoints(trip_id)
        else:
            print("⚠️  Skipping complete endpoints tests (no trip_id provided)")
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results Summary:")
        print(f"   Total Tests: {self.test_count}")
        print(f"   Passed: {self.pass_count}")
        print(f"   Failed: {self.fail_count}")
        print(f"   Success Rate: {(self.pass_count/self.test_count*100):.1f}%")
        
        success = self.fail_count == 0
        print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")
        
        if success:
            print("\n✅ Production deployment is working correctly!")
            print("   - Health endpoint is responding")
            print("   - Swagger docs include new endpoints")
            print("   - Short format is working")
            print("   - Modern format is working")
            if trip_id:
                print("   - Complete endpoints are working")
        else:
            print("\n❌ Production deployment has issues!")
            print("   Please check the failed tests and fix the issues.")
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Test production deployment")
    parser.add_argument("--api-base", default="https://mytrips-api.bahar.co.il", 
                       help="API base URL")
    parser.add_argument("--token", required=True,
                       help="Authorization token")
    parser.add_argument("--owner-id", required=True,
                       help="Owner ID for testing trips")
    parser.add_argument("--trip-id", 
                       help="Trip ID for testing complete endpoints (optional)")
    
    args = parser.parse_args()
    
    tester = ProductionTester(args.api_base, args.token)
    success = tester.run_full_test_suite(args.owner_id, args.trip_id)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
