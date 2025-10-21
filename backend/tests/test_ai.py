"""
Tests for AI route optimization endpoints
"""
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user_token):
    """Authentication headers fixture"""
    return {"Authorization": f"Bearer {test_user_token}"}


class TestAIRouteOptimization:
    """Test AI route optimization endpoint"""

    def test_health_endpoint(self, client):
        """Test AI health endpoint"""
        response = client.get("/ai/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-route-optimization"
        assert "openai_configured" in data
        assert "/ai/route-optimize" in data["endpoints"]

    def test_route_optimize_requires_auth(self, client):
        """Test that route optimization requires authentication"""
        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Test prompt",
                "data": "Test data",
                "response_structure": "Test structure",
            },
        )
        assert response.status_code == 401

    def test_route_optimize_validation(self, client, auth_headers):
        """Test request validation"""
        # Missing required fields
        response = client.post("/ai/route-optimize", json={}, headers=auth_headers)
        assert response.status_code == 422

        # Empty prompt
        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "",
                "data": "Test data",
                "response_structure": "Test structure",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Prompt too long
        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "x" * 2001,  # Exceeds max length
                "data": "Test data",
                "response_structure": "Test structure",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.api.ai.router.settings")
    def test_route_optimize_no_api_key(self, mock_settings, client, auth_headers):
        """Test behavior when OpenAI API key is not configured"""
        mock_settings.OPENAI_API_KEY = ""

        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Test prompt",
                "data": "Test data",
                "response_structure": "Test structure",
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "AI service not configured" in response.json()["detail"]

    @patch("app.api.ai.router.OpenAI")
    @patch("app.api.ai.router.settings")
    def test_route_optimize_success(
        self, mock_settings, mock_openai_class, client, auth_headers
    ):
        """Test successful route optimization"""
        # Mock settings
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.DEBUG = True

        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Optimized route result"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model_dump.return_value = {"test": "data"}

        mock_client.chat.completions.create.return_value = mock_response

        # Make request
        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Create the right order of the route",
                "data": "Start | 32.1878296, 34.9354013 | מיכל, כפר סבא",
                "response_structure": "Start: מיכל, כפר סבא (32.1878296, 34.9354013)",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["result"] == "Optimized route result"
        assert data["metadata"]["model"] == "gpt-4"
        assert data["metadata"]["tokens_used"]["total_tokens"] == 150
        assert (
            data["raw_response"] is not None
        )  # Should include raw response in debug mode

    @patch("app.api.ai.router.OpenAI")
    @patch("app.api.ai.router.settings")
    def test_route_optimize_openai_auth_error(
        self, mock_settings, mock_openai_class, client, auth_headers
    ):
        """Test OpenAI authentication error handling"""
        mock_settings.OPENAI_API_KEY = "invalid-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock OpenAI authentication error
        mock_error = Exception("Authentication failed")
        mock_error.response = Mock()
        mock_error.response.status_code = 401
        mock_client.chat.completions.create.side_effect = mock_error

        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Test prompt",
                "data": "Test data",
                "response_structure": "Test structure",
            },
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "AI service authentication failed" in response.json()["detail"]

    @patch("app.api.ai.router.OpenAI")
    @patch("app.api.ai.router.settings")
    def test_route_optimize_rate_limit_error(
        self, mock_settings, mock_openai_class, client, auth_headers
    ):
        """Test OpenAI rate limit error handling"""
        mock_settings.OPENAI_API_KEY = "test-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock OpenAI rate limit error
        mock_error = Exception("Rate limit exceeded")
        mock_error.response = Mock()
        mock_error.response.status_code = 429
        mock_client.chat.completions.create.side_effect = mock_error

        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Test prompt",
                "data": "Test data",
                "response_structure": "Test structure",
            },
            headers=auth_headers,
        )

        assert response.status_code == 429
        assert "temporarily unavailable due to high demand" in response.json()["detail"]

    @patch("app.api.ai.router.OpenAI")
    @patch("app.api.ai.router.settings")
    def test_route_optimize_with_structured_data(
        self, mock_settings, mock_openai_class, client, auth_headers
    ):
        """Test route optimization with structured data input"""
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.DEBUG = False

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Structured route result"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 60
        mock_response.usage.total_tokens = 180

        mock_client.chat.completions.create.return_value = mock_response

        # Test with structured data
        structured_data = {
            "stops": [
                {"name": "Start", "lat": 32.1878296, "lon": 34.9354013},
                {"name": "Stop 1", "lat": 32.1962854, "lon": 34.8766859},
            ]
        }

        response = client.post(
            "/ai/route-optimize",
            json={
                "prompt": "Optimize this route",
                "data": structured_data,
                "response_structure": "Start: Location (lat, lon)",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["result"] == "Structured route result"
        assert (
            data["raw_response"] is None
        )  # Should not include raw response when DEBUG=False

    def test_route_optimize_openai_import_error(self, client, auth_headers):
        """Test behavior when OpenAI package is not available"""
        with patch(
            "app.api.ai.router.OpenAI",
            side_effect=ImportError("No module named 'openai'"),
        ):
            response = client.post(
                "/ai/route-optimize",
                json={
                    "prompt": "Test prompt",
                    "data": "Test data",
                    "response_structure": "Test structure",
                },
                headers=auth_headers,
            )

            assert response.status_code == 500
            assert "AI service dependencies not available" in response.json()["detail"]
