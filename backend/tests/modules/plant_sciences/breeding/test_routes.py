"""
Tests for Breeding Operations Module.
"""

from fastapi.testclient import TestClient
from app.main import app


class TestBreedingRoutes:
    """Tests for /plant-sciences/breeding endpoints."""

    def test_dashboard_returns_200(self):
        """Test dashboard endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/plant-sciences/breeding/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            assert data["section"] == "breeding"
            assert "stats" in data

    def test_pipeline_returns_200(self):
        """Test pipeline endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/plant-sciences/breeding/pipeline")
            assert response.status_code == 200
            
            data = response.json()
            assert "stages" in data
            assert len(data["stages"]) > 0

    def test_genetic_gain_returns_200(self):
        """Test genetic gain endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/plant-sciences/breeding/genetic-gain")
            assert response.status_code == 200
            
            data = response.json()
            assert "overall_gain" in data
