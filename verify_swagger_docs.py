#!/usr/bin/env python3
"""
Verify that Swagger documentation includes the new endpoints
This script checks the OpenAPI schema for the new endpoints
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any, List

class SwaggerVerifier:
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base.rstrip('/')
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

    def get_openapi_schema(self) -> Dict[str, Any]:
        """Get OpenAPI schema from the API"""
        try:
            response = self.session.get(f"{self.api_base}/openapi.json")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get OpenAPI schema: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error getting OpenAPI schema: {str(e)}")
            return {}

    def verify_endpoint_exists(self, schema: Dict[str, Any], path: str, method: str = "get") -> bool:
        """Verify that an endpoint exists in the schema"""
        paths = schema.get("paths", {})
        if path not in paths:
            return False

        path_methods = paths[path]
        return method.lower() in path_methods

    def verify_response_model(self, schema: Dict[str, Any], path: str, method: str, expected_model: str) -> bool:
        """Verify that an endpoint has the expected response model"""
        paths = schema.get("paths", {})
        if path not in paths:
            return False

        path_methods = paths[path]
        if method.lower() not in path_methods:
            return False

        endpoint = path_methods[method.lower()]
        responses = endpoint.get("responses", {})
        success_response = responses.get("200", {})
        content = success_response.get("content", {})
        json_content = content.get("application/json", {})
        schema_ref = json_content.get("schema", {})

        # Check if the schema reference matches expected model
        ref = schema_ref.get("$ref", "")
        return expected_model in ref

    def verify_query_parameters(self, schema: Dict[str, Any], path: str, method: str, expected_params: List[str]) -> bool:
        """Verify that an endpoint has expected query parameters"""
        paths = schema.get("paths", {})
        if path not in paths:
            return False

        path_methods = paths[path]
        if method.lower() not in path_methods:
            return False

        endpoint = path_methods[method.lower()]
        parameters = endpoint.get("parameters", [])

        param_names = [param.get("name", "") for param in parameters if param.get("in") == "query"]

        for expected_param in expected_params:
            if expected_param not in param_names:
                return False

        return True

    def run_verification(self) -> bool:
        """Run all verification tests"""
        print("🔍 Verifying Swagger Documentation")
        print("=" * 50)

        # Get OpenAPI schema
        schema = self.get_openapi_schema()
        if not schema:
            print("❌ Could not retrieve OpenAPI schema - aborting verification")
            return False

        self.log_test("OpenAPI Schema Retrieved", True, f"Got schema with {len(schema.get('paths', {}))} endpoints")

        # Test 1: Verify complete endpoints exist
        endpoints_to_check = [
            ("/trips/{trip_id}/days/complete", "get", "DaysCompleteResponse"),
            ("/trips/{trip_id}/complete", "get", "TripCompleteResponse"),
        ]

        for path, method, response_model in endpoints_to_check:
            # Check endpoint exists
            exists = self.verify_endpoint_exists(schema, path, method)
            self.log_test(f"Endpoint Exists: {method.upper()} {path}", exists)

            if exists:
                # Check response model
                has_model = self.verify_response_model(schema, path, method, response_model)
                self.log_test(f"Response Model: {path} -> {response_model}", has_model)

        # Test 2: Verify trips endpoint has short format support
        trips_path = "/trips/"
        trips_exists = self.verify_endpoint_exists(schema, trips_path, "get")
        self.log_test(f"Endpoint Exists: GET {trips_path}", trips_exists)

        if trips_exists:
            # Check for format parameter
            has_format_param = self.verify_query_parameters(schema, trips_path, "get", ["format"])
            self.log_test("Format Parameter: /trips/ has format param", has_format_param)

            # Check for TripShortResponse in union
            has_short_response = self.verify_response_model(schema, trips_path, "get", "TripShortResponse")
            self.log_test("Short Response Model: /trips/ supports TripShortResponse", has_short_response)

        # Test 3: Verify query parameters for complete endpoints
        complete_params = ["include_place", "include_route_info", "status", "day_limit"]

        for path, _, _ in endpoints_to_check:
            if self.verify_endpoint_exists(schema, path, "get"):
                has_params = self.verify_query_parameters(schema, path, "get", complete_params)
                self.log_test(f"Query Parameters: {path}", has_params,
                            f"Expected: {', '.join(complete_params)}")

        # Test 4: Check for proper documentation
        paths = schema.get("paths", {})
        for path, _, _ in endpoints_to_check:
            if path in paths and "get" in paths[path]:
                endpoint = paths[path]["get"]
                has_summary = bool(endpoint.get("summary"))
                has_description = bool(endpoint.get("description"))
                self.log_test(f"Documentation: {path}", has_summary and has_description,
                            f"Summary: {has_summary}, Description: {has_description}")

        # Test 5: Print sample endpoint info
        print("\n📋 Sample Endpoint Information:")
        print("=" * 50)

        for path, method, _ in endpoints_to_check:
            if path in paths and method in paths[path]:
                endpoint = paths[path][method]
                print(f"\n🔗 {method.upper()} {path}")
                print(f"   Summary: {endpoint.get('summary', 'N/A')}")
                print(f"   Parameters: {len(endpoint.get('parameters', []))}")
                print(f"   Responses: {list(endpoint.get('responses', {}).keys())}")

        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Verification Summary:")
        print(f"   Total Tests: {self.test_count}")
        print(f"   Passed: {self.pass_count}")
        print(f"   Failed: {self.fail_count}")
        print(f"   Success Rate: {(self.pass_count/self.test_count*100):.1f}%")

        success = self.fail_count == 0
        print(f"\n{'🎉 All verifications passed!' if success else '❌ Some verifications failed!'}")

        if success:
            print("\n✅ Swagger documentation is properly updated!")
            print("   - New endpoints are documented")
            print("   - Response models are correct")
            print("   - Query parameters are included")
            print("   - Documentation strings are present")

        return success

def main():
    parser = argparse.ArgumentParser(description="Verify Swagger documentation")
    parser.add_argument("--api-base", default="http://localhost:8000",
                       help="API base URL")

    args = parser.parse_args()

    verifier = SwaggerVerifier(args.api_base)
    success = verifier.run_verification()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
