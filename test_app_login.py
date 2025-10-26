#!/usr/bin/env python3
"""
Test script for the new app login endpoint
"""
import requests
import json

# Test the app login endpoint
def test_app_login():
    base_url = "https://mytrips-api.bahar.co.il"
    
    # Test data
    test_cases = [
        {
            "name": "Valid user (if exists)",
            "email": "adar.bahar@gmail.com",
            "password": "mypassword"
        },
        {
            "name": "Invalid email",
            "email": "nonexistent@example.com", 
            "password": "anypassword"
        },
        {
            "name": "Invalid password",
            "email": "adar.bahar@gmail.com",
            "password": "wrongpassword"
        }
    ]
    
    print("🧪 Testing App Login Endpoint")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"   Email: {test_case['email']}")
        print(f"   Password: {test_case['password']}")
        
        try:
            response = requests.post(
                f"{base_url}/auth/app-login",
                json={
                    "email": test_case["email"],
                    "password": test_case["password"]
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                # Validate response structure
                required_fields = ["authenticated", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ❌ Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ Response structure valid")
                    
                    if data.get("authenticated"):
                        if "user_id" in data and data["user_id"]:
                            print(f"   ✅ User ID provided: {data['user_id']}")
                        else:
                            print(f"   ❌ Missing user_id for authenticated user")
                    else:
                        print(f"   ✅ Authentication failed as expected")
            else:
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON response: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("- The endpoint should return 200 status for all requests")
    print("- Response should have 'authenticated' and 'message' fields")
    print("- If authenticated=true, 'user_id' should be provided")
    print("- If authenticated=false, 'user_id' should be null")
    print("- No exceptions should be thrown")

if __name__ == "__main__":
    test_app_login()
