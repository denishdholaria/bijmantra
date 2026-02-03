"""
Unit tests for the crop suitability API.
"""
import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming your FastAPI app is named 'app'

client = TestClient(app)


def test_create_crop_suitability():
    """
    Test creating a crop suitability record.
    """
    response = client.post(
        "/api/v2/crop-suitability/",
        json={"crop_name": "test", "location_name": "test", "suitability_score": 0.5},
    )
    assert response.status_code == 200
    assert response.json()["crop_name"] == "test"


def test_get_crop_suitability_list():
    """
    Test getting a list of crop suitability records.
    """
    response = client.get("/api/v2/crop-suitability/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_crop_suitability():
    """
    Test getting a single crop suitability record.
    """
    response = client.get("/api/v2/crop-suitability/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_crop_suitability():
    """
    Test updating a crop suitability record.
    """
    response = client.put(
        "/api/v2/crop-suitability/1",
        json={"notes": "updated"},
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "updated"


def test_delete_crop_suitability():
    """
    Test deleting a crop suitability record.
    """
    response = client.delete("/api/v2/crop-suitability/1")
    assert response.status_code == 200


def test_analyze_crop_suitability():
    """
    Test the analyze endpoint.
    """
    response = client.post("/api/v2/crop-suitability/analyze?lat=10&lon=20&crop_name=test")
    assert response.status_code == 200
    assert response.json()["crop_name"] == "test"


def test_get_crop_suitability_map():
    """
    Test the map endpoint.
    """
    response = client.get("/api/v2/crop-suitability/map?lat=10&lon=20")
    assert response.status_code == 200
    assert "map_url" in response.json()
