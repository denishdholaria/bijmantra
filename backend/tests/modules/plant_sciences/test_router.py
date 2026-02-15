"""
Tests for Plant Sciences Module Router.
"""

from fastapi.testclient import TestClient
from app.main import app


class TestPlantSciencesRouter:
    """Tests for /plant-sciences/ endpoint."""

    def test_overview_returns_200(self):
        """Test that overview endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/plant-sciences/")
            assert response.status_code == 200

    def test_overview_structure(self):
        """Test overview response structure."""
        with TestClient(app) as client:
            response = client.get("/plant-sciences/")
            data = response.json()
            
            assert data["division"] == "plant-sciences"
            assert data["status"] == "active"
            assert "subsections" in data
            assert len(data["subsections"]) > 0
