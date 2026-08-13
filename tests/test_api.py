"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
    
    def test_basic_health_check(self):
        """Test basic health endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_liveness_probe(self):
        """Test liveness probe."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_readiness_probe(self):
        """Test readiness probe."""
        response = client.get("/api/v1/health/ready")
        # May return 200 or 503 depending on system state
        assert response.status_code in [200, 503]


class TestAnalysisEndpoints:
    """Test analysis endpoints."""
    
    def test_analyze_endpoint_validation(self):
        """Test analysis endpoint with invalid input."""
        response = client.post(
            "/api/v1/analyze",
            json={"source": "", "language": "english"}
        )
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_analyze_endpoint_invalid_language(self):
        """Test analysis with invalid language."""
        response = client.post(
            "/api/v1/analyze",
            json={
                "source": "https://www.youtube.com/watch?v=test",
                "language": "spanish"
            }
        )
        # Should fail validation
        assert response.status_code == 422


class TestChatEndpoints:
    """Test chat endpoints."""
    
    def test_chat_endpoint_validation(self):
        """Test chat endpoint with invalid input."""
        response = client.post(
            "/api/v1/chat",
            json={"question": "Hi"}  # Too short
        )
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_chat_endpoint_empty_question(self):
        """Test chat with empty question."""
        response = client.post(
            "/api/v1/chat",
            json={"question": ""}
        )
        assert response.status_code == 422
    
    def test_clear_session_endpoint(self):
        """Test clearing chat session."""
        response = client.delete("/api/v1/chat/session/test123")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test123"


class TestMiddleware:
    """Test middleware functionality."""
    
    def test_cors_headers(self):
        """Test CORS middleware."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_process_time_header(self):
        """Test that process time header is added."""
        response = client.get("/api/v1/health")
        assert "x-process-time" in response.headers
        assert float(response.headers["x-process-time"]) >= 0


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 error handling."""
        response = client.post("/api/v1/health")  # GET only endpoint
        assert response.status_code == 405
