"""
Tests for BrAPI v2 public endpoints (no auth required).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestServerInfo:
    """Tests for /brapi/v2/serverinfo endpoint."""

    def test_get_serverinfo_returns_200(self):
        """Test that serverinfo endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            assert response.status_code == 200

    def test_serverinfo_has_correct_structure(self):
        """Test that serverinfo response has BrAPI structure."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            data = response.json()
            
            # Check BrAPI response structure
            assert "metadata" in data
            assert "result" in data
            
            # Check result fields
            result = data["result"]
            assert "serverName" in result
            assert "organizationName" in result

    def test_serverinfo_contains_bijmantra(self):
        """Test that serverinfo identifies as Bijmantra."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            result = response.json()["result"]
            
            assert "Bijmantra" in result["serverName"]


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self):
        """Test health endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_returns_status(self):
        """Test health endpoint returns status information."""
        with TestClient(app) as client:
            response = client.get("/health")
            data = response.json()
            assert "status" in data


class TestRootEndpoint:
    """Tests for root / endpoint."""

    def test_root_returns_200(self):
        """Test root endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_root_returns_welcome(self):
        """Test root endpoint returns welcome message."""
        with TestClient(app) as client:
            response = client.get("/")
            data = response.json()
            assert "message" in data or "status" in data
