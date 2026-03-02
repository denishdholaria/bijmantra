import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.core import User
from app.api import deps
from app.services.biosimulation import biosimulation_service

@pytest.mark.asyncio
async def test_run_simulation_uses_user_organization_id():
    client = TestClient(app)

    # Mock user
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.organization_id = 10  # Specific ID to test
    mock_user.is_active = True

    # Mock DB
    mock_db = AsyncMock()

    # Override dependencies
    app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user
    app.dependency_overrides[deps.get_db] = lambda: mock_db

    # Mock the service method return value
    mock_run_result = MagicMock()
    mock_run_result.id = 123
    mock_run_result.predicted_flowering_date = datetime(2023, 7, 15)
    mock_run_result.predicted_maturity_date = datetime(2023, 9, 1)
    mock_run_result.predicted_yield = 500.0
    mock_run_result.status = "COMPLETED"

    # Patch the run_simulation method
    with patch.object(biosimulation_service, "run_simulation", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_run_result

        payload = {
            "crop_model_id": 5,
            "location_id": 2,
            "start_date": "2023-05-01T00:00:00",
            "daily_weather_data": [{"t_max": 30, "t_min": 20}]
        }

        # Act
        response = client.post("/api/v2/biosimulation/run", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == 123

        # Verify call arguments
        # Check kwargs
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["organization_id"] == 10
        assert call_kwargs["crop_model_id"] == 5

    # Cleanup overrides
    app.dependency_overrides = {}
