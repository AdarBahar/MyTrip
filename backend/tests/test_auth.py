"""
Tests for authentication API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.models.user import User


class TestAuthLogin:
    """Test authentication login endpoint"""

    def test_login_with_valid_email(self, client: TestClient, db_session):
        """Test login with a valid email address"""
        response = client.post(
            "/auth/login",
            json={"email": "newuser@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user_data = data["user"]
        assert user_data["email"] == "newuser@example.com"
        assert "id" in user_data
        assert "display_name" in user_data
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_login_with_existing_user(self, client: TestClient, test_user: User):
        """Test login with an existing user"""
        response = client.post(
            "/auth/login",
            json={"email": test_user.email}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that existing user data is returned
        user_data = data["user"]
        assert user_data["email"] == test_user.email
        assert user_data["id"] == test_user.id
        assert user_data["display_name"] == test_user.display_name

    def test_login_with_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format"""
        response = client.post(
            "/auth/login",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_with_missing_email(self, client: TestClient):
        """Test login with missing email field"""
        response = client.post(
            "/auth/login",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_with_empty_email(self, client: TestClient):
        """Test login with empty email"""
        response = client.post(
            "/auth/login",
            json={"email": ""}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_with_null_email(self, client: TestClient):
        """Test login with null email"""
        response = client.post(
            "/auth/login",
            json={"email": None}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_content_type_validation(self, client: TestClient):
        """Test that login requires JSON content type"""
        response = client.post(
            "/auth/login",
            content="email=test@example.com",  # Form data instead of JSON
            headers={"content-type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    def test_login_generates_valid_token_format(self, client: TestClient):
        """Test that login generates a token in the expected format"""
        response = client.post(
            "/auth/login",
            json={"email": "tokentest@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        token = data["access_token"]
        assert token.startswith("fake_token_")
        assert len(token) > 11  # Should have user ID after prefix

    def test_login_creates_display_name_from_email(self, client: TestClient, db_session):
        """Test that display name is created from email"""
        response = client.post(
            "/auth/login",
            json={"email": "john.doe@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that display name was generated
        user_data = data["user"]
        assert user_data["display_name"] == "John Doe"
        
        # Verify in database
        user = db_session.query(User).filter(User.email == "john.doe@example.com").first()
        assert user.display_name == "John Doe"

    def test_multiple_logins_same_user(self, client: TestClient, test_user: User):
        """Test multiple logins with the same user"""
        # First login
        response1 = client.post(
            "/auth/login",
            json={"email": test_user.email}
        )
        
        # Second login
        response2 = client.post(
            "/auth/login",
            json={"email": test_user.email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should return the same user data
        user1 = response1.json()["user"]
        user2 = response2.json()["user"]
        
        assert user1["id"] == user2["id"]
        assert user1["email"] == user2["email"]
