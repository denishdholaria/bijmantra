"""
Tests for IoT Telemetry API.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.core import User
from app.models.iot import IoTTelemetry

# Mock User
mock_user = User(id=1, email="test@example.com", is_active=True, organization_id=1)

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

class TestTelemetry:

    @patch("app.api.v2.iot.telemetry.telemetry_service")
    def test_record_reading(self, mock_service):
        """Test recording a reading."""
        # Return a real object or a mock that passes Pydantic validation
        mock_telemetry = IoTTelemetry(
            id=1,
            timestamp=datetime.now(),
            device_id=1,
            sensor_id=1,
            value=25.5,
            quality="good"
        )

        mock_service.record_reading = AsyncMock(return_value=mock_telemetry)

        payload = {
            "device_db_id": "test-device-01",
            "sensor_code": "temp",
            "value": 25.5,
            "quality": "good"
        }

        response = client.post("/api/v2/iot/telemetry/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["value"] == 25.5
        assert data["device_id"] == 1

    @patch("app.api.v2.iot.telemetry.telemetry_service")
    def test_get_readings(self, mock_service):
        """Test getting readings."""
        mock_telemetry = IoTTelemetry(
            id=1,
            timestamp=datetime.now(),
            device_id=1,
            sensor_id=1,
            value=25.5,
            quality="good"
        )

        mock_service.get_readings = AsyncMock(return_value=([mock_telemetry], 1))

        response = client.get("/api/v2/iot/telemetry/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["value"] == 25.5
