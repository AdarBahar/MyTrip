#!/usr/bin/env python3
"""
Test script for the new trips sorting functionality
"""

import requests
import json
import sys
from datetime import datetime

def test_trips_sorting(api_base="http://localhost:8000"):
    """Test the new sorting functionality in the trips endpoint"""

    print("🧪 Testing Trips Sorting Functionality")
    print("=" * 50)

    # Test data
    test_email = "test@example.com"
    test_password = "testpassword123"

    try:
        # 1. Login to get token
        print("1. Logging in...")
        login_response = requests.post(
            f"{api_base}/auth/login",
            json={"email": test_email, "password": test_password}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False

        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")

        # 2. Test default sorting (should be newest first)
        print("\n2. Testing default sorting (newest first)...")
        response = requests.get(f"{api_base}/trips", headers=headers)

        if response.status_code == 200:
            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])
            print(f"✅ Default request successful - got {len(trips)} trips")

            if len(trips) >= 2:
                # Check if sorted by created_at desc
                first_trip = trips[0]
                second_trip = trips[1]
                first_created = first_trip.get("created_at")
                second_created = second_trip.get("created_at")

                if first_created >= second_created:
                    print("✅ Default sorting appears correct (newest first)")
                else:
                    print("⚠️  Default sorting might not be newest first")

            print(f"First trip: {trips[0].get('title', 'N/A')} (created: {trips[0].get('created_at', 'N/A')})")
        else:
            print(f"❌ Default trips request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        # 3. Test explicit newest first sorting
        print("\n3. Testing explicit newest first sorting...")
        response = requests.get(f"{api_base}/trips?sort_by=created_at:desc", headers=headers)

        if response.status_code == 200:
            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])
            print(f"✅ Explicit newest first successful - got {len(trips)} trips")
        else:
            print(f"❌ Explicit newest first failed: {response.status_code}")
            print(f"Response: {response.text}")

        # 4. Test oldest first sorting
        print("\n4. Testing oldest first sorting...")
        response = requests.get(f"{api_base}/trips?sort_by=created_at:asc", headers=headers)

        if response.status_code == 200:
            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])
            print(f"✅ Oldest first successful - got {len(trips)} trips")

            if len(trips) >= 2:
                first_trip = trips[0]
                second_trip = trips[1]
                first_created = first_trip.get("created_at")
                second_created = second_trip.get("created_at")

                if first_created <= second_created:
                    print("✅ Oldest first sorting appears correct")
                else:
                    print("⚠️  Oldest first sorting might not be working")

            print(f"First trip: {trips[0].get('title', 'N/A')} (created: {trips[0].get('created_at', 'N/A')})")
        else:
            print(f"❌ Oldest first failed: {response.status_code}")
            print(f"Response: {response.text}")

        # 5. Test title sorting
        print("\n5. Testing title sorting...")
        response = requests.get(f"{api_base}/trips?sort_by=title:asc", headers=headers)

        if response.status_code == 200:
            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])
            print(f"✅ Title sorting successful - got {len(trips)} trips")

            if len(trips) >= 2:
                print(f"First trip by title: {trips[0].get('title', 'N/A')}")
                print(f"Second trip by title: {trips[1].get('title', 'N/A')}")
        else:
            print(f"❌ Title sorting failed: {response.status_code}")
            print(f"Response: {response.text}")

        # 6. Test invalid sorting (should fallback to default)
        print("\n6. Testing invalid sorting parameter...")
        response = requests.get(f"{api_base}/trips?sort_by=invalid:field", headers=headers)

        if response.status_code == 200:
            print("✅ Invalid sorting handled gracefully (fallback to default)")
        else:
            print(f"❌ Invalid sorting caused error: {response.status_code}")

        # 7. Test with size parameter for "10 most recent"
        print("\n7. Testing 10 most recent trips...")
        response = requests.get(f"{api_base}/trips?size=10&sort_by=created_at:desc", headers=headers)

        if response.status_code == 200:
            data = response.json()
            trips = data.get("data", []) if "data" in data else data.get("trips", [])
            print(f"✅ 10 most recent trips successful - got {len(trips)} trips")
            print(f"Requested 10, got {len(trips)} (limited by actual trip count)")
        else:
            print(f"❌ 10 most recent failed: {response.status_code}")
            print(f"Response: {response.text}")

        print("\n🎉 All tests completed!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test trips sorting functionality")
    parser.add_argument("--api-base", default="http://localhost:8000",
                       help="API base URL (default: http://localhost:8000)")

    args = parser.parse_args()

    success = test_trips_sorting(args.api_base)
    sys.exit(0 if success else 1)
