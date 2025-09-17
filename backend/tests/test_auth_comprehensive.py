"""
Comprehensive authentication test suite for JWT migration
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.auth
class TestCurrentAuthentication:
    """Test current fake authentication system (baseline before JWT migration)"""
    
    def test_fake_auth_valid_token(self, client: TestClient, test_user, auth_headers):
        """Test that valid fake token works"""
        response = client.get("/trips/", headers=auth_headers)
        assert response.status_code == 200
        
    def test_fake_auth_invalid_token(self, client: TestClient):
        """Test that invalid token fails"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/trips/", headers=invalid_headers)
        assert response.status_code == 401
        
    def test_fake_auth_missing_token(self, client: TestClient):
        """Test that missing token fails"""
        response = client.get("/trips/")
        assert response.status_code == 401
        
    def test_fake_auth_malformed_header(self, client: TestClient):
        """Test various malformed authentication headers"""
        test_cases = [
            "fake_token_123",  # Missing Bearer
            "Bearer",  # Missing token
            "Basic fake_token_123",  # Wrong scheme
            "Bearer fake_token_",  # Empty user ID
            "",  # Empty header
        ]
        
        for auth_header in test_cases:
            headers = {"Authorization": auth_header} if auth_header else {}
            response = client.get("/trips/", headers=headers)
            assert response.status_code == 401, f"Expected 401 for header: '{auth_header}'"


@pytest.mark.auth
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security aspects"""
    
    def test_protected_endpoints_require_auth(self, client: TestClient):
        """Test that all protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/trips/"),
            ("POST", "/trips/"),
            ("GET", "/trips/test-trip"),
            ("PUT", "/trips/test-trip"),
            ("DELETE", "/trips/test-trip"),
            ("GET", "/trips/test-trip/days"),
            ("POST", "/trips/test-trip/days"),
        ]
        
        for method, endpoint in protected_endpoints:
            response = getattr(client, method.lower())(endpoint)
            assert response.status_code == 401, f"Expected 401 for {method} {endpoint}"
            
    def test_user_isolation(self, client: TestClient, db_session, test_data_factory):
        """Test that users can only access their own data"""
        # Create two users
        from app.models.user import User
        
        user1 = User(email="user1@test.com", display_name="User 1")
        user2 = User(email="user2@test.com", display_name="User 2")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create trip for user1
        trip_data = test_data_factory.create_trip_data(title="User 1 Trip")
        user1_headers = {"Authorization": f"Bearer fake_token_{user1.id}"}
        response = client.post("/trips/", json=trip_data, headers=user1_headers)
        assert response.status_code == 201
        trip_slug = response.json()["slug"]
        
        # User2 should not be able to access user1's trip
        user2_headers = {"Authorization": f"Bearer fake_token_{user2.id}"}
        response = client.get(f"/trips/{trip_slug}", headers=user2_headers)
        assert response.status_code in [403, 404]  # Forbidden or Not Found


@pytest.mark.auth
@pytest.mark.performance
class TestAuthenticationPerformance:
    """Test authentication performance"""
    
    def test_auth_response_time(self, client: TestClient, auth_headers):
        """Test that authentication doesn't significantly slow down requests"""
        import time
        
        start_time = time.time()
        response = client.get("/trips/", headers=auth_headers)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, f"Request took {elapsed_time:.2f}s (should be < 1.0s)"
        
    def test_multiple_concurrent_auth_requests(self, client: TestClient, auth_headers):
        """Test handling multiple concurrent authenticated requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/trips/", headers=auth_headers)
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


@pytest.mark.auth
@pytest.mark.regression
class TestAuthenticationRegression:
    """Regression tests to ensure authentication changes don't break existing functionality"""
    
    def test_trip_crud_with_auth(self, client: TestClient, auth_headers, test_data_factory):
        """Test complete CRUD operations with authentication"""
        # Create trip
        trip_data = test_data_factory.create_trip_data()
        response = client.post("/trips/", json=trip_data, headers=auth_headers)
        assert response.status_code == 201
        trip_slug = response.json()["slug"]
        
        # Read trip
        response = client.get(f"/trips/{trip_slug}", headers=auth_headers)
        assert response.status_code == 200
        
        # Update trip
        updated_data = {**trip_data, "title": "Updated Trip Title"}
        response = client.put(f"/trips/{trip_slug}", json=updated_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Delete trip
        response = client.delete(f"/trips/{trip_slug}", headers=auth_headers)
        assert response.status_code == 200
        
    def test_health_check_no_auth_required(self, client: TestClient):
        """Test that health check doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.jwt
class TestJWTAuthentication:
    """Test JWT authentication implementation"""

    def test_jwt_login_success(self, client: TestClient, test_user):
        """Test successful JWT login"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        response = client.post("/auth/jwt/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data

        # Validate JWT structure
        access_token = data["access_token"]
        assert_jwt_token_structure(access_token)

        refresh_token = data["refresh_token"]
        assert_jwt_token_structure(refresh_token)

        # Validate user data
        user_data = data["user"]
        assert user_data["email"] == test_user.email
        assert user_data["id"] == test_user.id

    def test_jwt_login_missing_password(self, client: TestClient, test_user):
        """Test JWT login without password"""
        login_data = {
            "email": test_user.email
        }
        response = client.post("/auth/jwt/login", json=login_data)

        assert response.status_code == 422  # Validation error

    def test_jwt_login_empty_password(self, client: TestClient, test_user):
        """Test JWT login with empty password"""
        login_data = {
            "email": test_user.email,
            "password": ""
        }
        response = client.post("/auth/jwt/login", json=login_data)

        assert response.status_code == 401

    def test_jwt_login_nonexistent_user(self, client: TestClient):
        """Test JWT login with nonexistent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
        response = client.post("/auth/jwt/login", json=login_data)

        assert response.status_code == 401

    def test_jwt_token_refresh(self, client: TestClient, test_user):
        """Test JWT token refresh"""
        # First login to get tokens
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        login_response = client.post("/auth/jwt/login", json=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Test refresh
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/jwt/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # New access token should be different
        new_access_token = data["access_token"]
        assert new_access_token != tokens["access_token"]
        assert_jwt_token_structure(new_access_token)

    def test_jwt_token_refresh_invalid_token(self, client: TestClient):
        """Test JWT token refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/auth/jwt/refresh", json=refresh_data)

        assert response.status_code == 401

    def test_jwt_logout(self, client: TestClient):
        """Test JWT logout"""
        response = client.post("/auth/jwt/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_jwt_validate_token(self, client: TestClient, test_user):
        """Test JWT token validation"""
        # First login to get token
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        login_response = client.post("/auth/jwt/login", json=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        access_token = tokens["access_token"]

        # Test validation
        response = client.get(f"/auth/jwt/validate?token={access_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user" in data
        assert data["user"]["email"] == test_user.email

    def test_jwt_validate_invalid_token(self, client: TestClient):
        """Test JWT token validation with invalid token"""
        response = client.get("/auth/jwt/validate?token=invalid_token")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_jwt_health_check(self, client: TestClient):
        """Test JWT health check endpoint"""
        response = client.get("/auth/jwt/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jwt-authentication"
        assert "endpoints" in data


# Utility functions for authentication testing
def create_test_user_with_password(db_session, email: str, password: str = "testpass123"):
    """Create a test user with password hash (for JWT testing)"""
    from app.models.user import User
    # This will be updated when we implement password hashing
    user = User(
        email=email,
        display_name=f"Test User {email}",
        password_hash=f"hashed_{password}"  # Placeholder
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def assert_jwt_token_structure(token: str):
    """Assert that a token has valid JWT structure (for future JWT tests)"""
    parts = token.split('.')
    assert len(parts) == 3, "JWT should have 3 parts separated by dots"
    # Additional JWT validation will be added when implementing JWT


# Test data for authentication scenarios
@pytest.fixture
def auth_test_scenarios():
    """Provide various authentication test scenarios"""
    return {
        "valid_login": {
            "email": "test@example.com",
            "password": "validpassword123"
        },
        "invalid_email": {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        },
        "invalid_password": {
            "email": "test@example.com",
            "password": "wrongpassword"
        },
        "malformed_email": {
            "email": "not-an-email",
            "password": "password123"
        },
        "empty_credentials": {
            "email": "",
            "password": ""
        }
    }


@pytest.mark.auth
class TestAuthenticationEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_authorization_header(self, client: TestClient):
        """Test empty authorization header"""
        headers = {"Authorization": ""}
        response = client.get("/trips/", headers=headers)
        assert response.status_code == 401
        
    def test_malformed_bearer_token(self, client: TestClient):
        """Test malformed bearer tokens"""
        malformed_tokens = [
            "Bearer ",  # Empty token
            "Bearer token_without_prefix",  # Missing fake_token_ prefix
            "Bearer fake_token_",  # Empty user ID
            "Bearer fake_token_invalid_user_id_format",  # Invalid format
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = client.get("/trips/", headers=headers)
            assert response.status_code == 401, f"Expected 401 for token: {token}"
            
    def test_case_sensitive_bearer_scheme(self, client: TestClient, test_user):
        """Test that Bearer scheme is case-sensitive"""
        test_cases = [
            f"bearer fake_token_{test_user.id}",  # lowercase
            f"BEARER fake_token_{test_user.id}",  # uppercase
            f"Bearer fake_token_{test_user.id}",  # correct case
        ]
        
        for auth_header in test_cases:
            headers = {"Authorization": auth_header}
            response = client.get("/trips/", headers=headers)
            # Only the correct case should work
            if auth_header.startswith("Bearer "):
                assert response.status_code == 200
            else:
                assert response.status_code == 401
