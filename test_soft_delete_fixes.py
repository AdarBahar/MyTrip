#!/usr/bin/env python3
"""
Test script for soft delete fixes
Run this after deploying the changes to verify everything works correctly
"""

import requests
import json
import sys
from typing import Optional

# Configuration
BASE_URL = "https://mytrips-api.bahar.co.il"
# You'll need to provide a valid token
AUTH_TOKEN = "your_auth_token_here"

def make_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make an authenticated API request"""
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"{method} {endpoint} -> {response.status_code}")

        if response.status_code >= 400:
            print(f"Error: {response.text}")
            return {"error": response.text, "status_code": response.status_code}

        if response.status_code == 204:  # No content
            return {"success": True, "status_code": 204}

        return response.json()

    except Exception as e:
        print(f"Request failed: {e}")
        return {"error": str(e)}

def test_stops_summary_includes_days(trip_id: str):
    """Test that stops summary includes days count"""
    print("\n🧪 Testing stops summary includes days count...")

    result = make_request("GET", f"/stops/{trip_id}/stops/summary")

    if "error" in result:
        print("❌ Failed to get stops summary")
        return False

    if "days" not in result:
        print("❌ Stops summary missing 'days' field")
        return False

    print(f"✅ Stops summary includes days count: {result['days']}")
    print(f"   Total stops: {result.get('total_stops', 'N/A')}")
    return True

def test_routing_active_summary_includes_status(day_id: str):
    """Test that routing active summary includes status"""
    print(f"\n🧪 Testing routing active summary includes status for day {day_id}...")

    result = make_request("GET", f"/routing/days/{day_id}/active-summary")

    if "error" in result:
        print("❌ Failed to get routing active summary")
        return False

    if "status" not in result:
        print("❌ Routing active summary missing 'status' field")
        return False

    print(f"✅ Routing active summary includes status: {result['status']}")
    return True

def test_day_deletion_and_status_change(trip_id: str, day_id: str):
    """Test day deletion sets status to deleted and cascades to stops"""
    print(f"\n🧪 Testing day deletion for day {day_id}...")

    # First, get the day to see current status
    print("Getting day before deletion...")
    day_before = make_request("GET", f"/trips/{trip_id}/days/{day_id}")
    if "error" not in day_before:
        print(f"   Day status before: {day_before.get('status', 'unknown')}")

    # Get stops before deletion
    print("Getting stops before deletion...")
    stops_before = make_request("GET", f"/trips/{trip_id}/days/{day_id}/stops")
    if "error" not in stops_before:
        stop_count_before = len(stops_before.get('stops', []))
        print(f"   Stops count before: {stop_count_before}")

    # Delete the day
    print("Deleting day...")
    delete_result = make_request("DELETE", f"/trips/{trip_id}/days/{day_id}")

    if delete_result.get("status_code") != 204:
        print("❌ Day deletion failed")
        return False

    print("✅ Day deletion returned 204 No Content")

    # Try to get the day after deletion (should return 404)
    print("Checking day is no longer accessible...")
    day_after = make_request("GET", f"/trips/{trip_id}/days/{day_id}")
    if day_after.get("status_code") == 404:
        print("✅ Day is no longer accessible (404)")
    else:
        print("❌ Day is still accessible after deletion")
        return False

    # Check stops are no longer accessible
    print("Checking stops are no longer accessible...")
    stops_after = make_request("GET", f"/trips/{trip_id}/days/{day_id}/stops")
    if "error" in stops_after or len(stops_after.get('stops', [])) == 0:
        print("✅ Stops are no longer accessible or empty")
    else:
        print("❌ Stops are still accessible after day deletion")
        return False

    return True

def main():
    """Main test function"""
    print("🚀 Testing Soft Delete Fixes")
    print("=" * 50)

    if AUTH_TOKEN == "your_auth_token_here":
        print("❌ Please set a valid AUTH_TOKEN in the script")
        sys.exit(1)

    # You'll need to provide valid IDs for testing
    trip_id = input("Enter a trip ID to test: ").strip()
    if not trip_id:
        print("❌ Trip ID is required")
        sys.exit(1)

    day_id = input("Enter a day ID to test deletion (WARNING: This will delete the day!): ").strip()

    # Test 1: Stops summary includes days
    test1_passed = test_stops_summary_includes_days(trip_id)

    # Test 2: Routing active summary includes status (if day_id provided)
    test2_passed = True
    if day_id:
        test2_passed = test_routing_active_summary_includes_status(day_id)

    # Test 3: Day deletion (if day_id provided and user confirms)
    test3_passed = True
    if day_id:
        confirm = input(f"\n⚠️  Are you sure you want to delete day {day_id}? This cannot be undone! (yes/no): ").strip().lower()
        if confirm == "yes":
            test3_passed = test_day_deletion_and_status_change(trip_id, day_id)
        else:
            print("Skipping day deletion test")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Stops summary includes days: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Routing summary includes status: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"   Day deletion and cascade: {'✅ PASS' if test3_passed else '❌ FAIL'}")

    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
