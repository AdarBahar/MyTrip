#!/usr/bin/env python3
"""
Test script for AI route optimization endpoint

This script demonstrates how to use the new AI route optimization endpoint
to get intelligent route suggestions using OpenAI's GPT models.

Usage:
    python tools/test_ai_route_optimization.py

Requirements:
    - Backend server running with OpenAI API key configured
    - Valid authentication token
"""

import json
import requests
from typing import Dict, Any


# Configuration
BASE_URL = "https://mytrips-api.bahar.co.il"  # Update with your API base URL
# BASE_URL = "http://localhost:8000"  # For local development

# You'll need to get a valid token from the auth endpoint
AUTH_TOKEN = "your-auth-token-here"  # Replace with actual token


def test_ai_health():
    """Test the AI health endpoint"""
    print("🔍 Testing AI health endpoint...")

    response = requests.get(f"{BASE_URL}/ai/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ AI service is healthy")
        print(f"   OpenAI configured: {data.get('openai_configured', False)}")
        print(f"   Available endpoints: {data.get('endpoints', [])}")
    else:
        print(f"❌ AI health check failed: {response.status_code}")
        print(f"   Response: {response.text}")

    return response.status_code == 200


def test_ai_route_optimization():
    """Test the AI route optimization endpoint"""
    print("\n🤖 Testing AI route optimization...")

    # Example route data from Israel
    request_data = {
        "prompt": "Create the right order of the route, assuming that start and end are book-endings, and stops are ordered in the optimized route. If a stop is marked as fixed, order for that specific stop should not change.",
        "data": """Type | Location | Address
Start | 32.1878296, 34.9354013 | מיכל, כפר סבא, ישראל
End | 32.067444, 34.7936703 | יגאל אלון, 6789731 תל־אביב–יפו, ישראל
Stop | 32.1962854, 34.8766859 | רננים, רעננה, ישראל
Stop | 32.1739447, 34.8081801 | הרצליה פיתוח, הרצליה, ישראל
Stop | 32.1879896, 34.8934844 | כפר סבא הירוקה, כפר סבא, ישראל""",
        "response_structure": """Start: מיכל, כפר סבא (32.1878296, 34.9354013)
Stop 1: כפר סבא הירוקה (32.1879896, 34.8934844)
Stop 2: רננים, רעננה (32.1962854, 34.8766859)
Stop 3: הרצליה פיתוח (32.1739447, 34.8081801)
End: יגאל אלון, תל אביב–יפו (32.067444, 34.7936703)"""
    }

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"📤 Sending request to {BASE_URL}/ai/route-optimize")
    print(f"   Prompt: {request_data['prompt'][:100]}...")

    response = requests.post(
        f"{BASE_URL}/ai/route-optimize",
        json=request_data,
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ AI route optimization successful!")
        print(f"\n📍 Optimized Route:")
        print(data["result"])

        if "metadata" in data:
            metadata = data["metadata"]
            print(f"\n📊 Metadata:")
            print(f"   Model: {metadata.get('model', 'N/A')}")
            if "tokens_used" in metadata:
                tokens = metadata["tokens_used"]
                print(f"   Tokens used: {tokens.get('total_tokens', 'N/A')} "
                      f"(prompt: {tokens.get('prompt_tokens', 'N/A')}, "
                      f"completion: {tokens.get('completion_tokens', 'N/A')})")

        return True
    else:
        print(f"❌ AI route optimization failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Response: {response.text}")

        return False


def test_different_prompts():
    """Test with different types of prompts"""
    print("\n🎯 Testing different prompt types...")

    test_cases = [
        {
            "name": "Simple optimization",
            "prompt": "Optimize the route for shortest travel time",
            "data": "Start: Tel Aviv\nStop: Ramat Gan\nStop: Petah Tikva\nEnd: Herzliya",
            "response_structure": "1. Start location\n2. Stop location\n3. End location"
        },
        {
            "name": "Fixed constraints",
            "prompt": "Optimize route but keep the second stop fixed in position",
            "data": "Start: Jerusalem\nStop: Bethlehem (FIXED)\nStop: Hebron\nEnd: Beersheba",
            "response_structure": "Start -> Stop 1 -> Stop 2 -> End"
        },
        {
            "name": "Scenic route",
            "prompt": "Create a scenic route that prioritizes beautiful views over speed",
            "data": "Start: Haifa\nStop: Nazareth\nStop: Tiberias\nEnd: Safed",
            "response_structure": "Scenic Route: Location 1 -> Location 2 -> Location 3 -> Location 4"
        }
    ]

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")

        response = requests.post(
            f"{BASE_URL}/ai/route-optimize",
            json=test_case,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"   Result: {data['result'][:100]}...")
        else:
            print(f"❌ Failed: {response.status_code}")


def main():
    """Main test function"""
    print("🚀 AI Route Optimization Test Suite")
    print("=" * 50)

    # Check if auth token is configured
    if AUTH_TOKEN == "your-auth-token-here":
        print("⚠️  Please update AUTH_TOKEN with a valid authentication token")
        print("   You can get a token by calling the /auth/login endpoint")
        return

    # Test health endpoint
    if not test_ai_health():
        print("❌ AI service is not available. Please check:")
        print("   1. Backend server is running")
        print("   2. OpenAI API key is configured")
        print("   3. OpenAI package is installed")
        return

    # Test route optimization
    if test_ai_route_optimization():
        # Test different prompt types
        test_different_prompts()

    print("\n🎉 Test suite completed!")


if __name__ == "__main__":
    main()
