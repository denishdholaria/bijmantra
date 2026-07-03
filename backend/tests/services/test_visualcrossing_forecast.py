"""
Unit tests for Visual Crossing Forecast Fetching in Weather Integration Service
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.environment.services.weather_integration_service import (
    WeatherIntegrationService,
    TemperatureData,
    WeatherProvider,
    DataQuality
)

@pytest.fixture
def weather_service():
    """Create weather integration service instance"""
    service = WeatherIntegrationService()
    service.visualcrossing_key = "test_key"
    return service

@pytest.mark.asyncio
async def test_fetch_visualcrossing_forecast_success(weather_service):
    """Test successful forecast fetch from Visual Crossing"""
    # Mock HTTP client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "days": [
            {
                "datetime": "2026-02-20",
                "tempmax": 20.0,
                "tempmin": 10.0,
                "temp": 15.0,
                "precip": 0.5,
                "humidity": 60,
                "windspeed": 10.0
            },
            {
                "datetime": "2026-02-21",
                "tempmax": 22.0,
                "tempmin": 12.0,
                "temp": 17.0,
                "precip": 0.0,
                "humidity": 55,
                "windspeed": 8.0
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client

    # Fetch forecast
    # Use dates that are definitely in the future relative to when this test might run,
    # but we will mock date.today to be sure
    test_today = date(2026, 2, 15)
    dates = [date(2026, 2, 20), date(2026, 2, 21)]

    with patch("app.modules.environment.services.weather_integration_service.date") as mock_date:
        mock_date.today.return_value = test_today
        # This is needed because date() is used to create date objects
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        data = await weather_service._fetch_visualcrossing_forecast(
            latitude=40.7128,
            longitude=-74.0060,
            dates=dates
        )

    assert len(data) == 2
    assert data[0].date == date(2026, 2, 20)
    assert data[0].temp_max == 20.0
    assert data[0].temp_min == 10.0
    assert data[0].is_forecast is True
    assert data[0].source == WeatherProvider.VISUAL_CROSSING
    assert data[0].quality == DataQuality.GOOD
    assert data[0].precipitation == 0.5
    assert data[0].humidity == 60
    assert data[0].wind_speed == 10.0

    # Verify URL construction
    days_ahead = (date(2026, 2, 21) - test_today).days
    expected_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/40.7128,-74.006/next{days_ahead}days"
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert args[0] == expected_url

@pytest.mark.asyncio
async def test_fetch_visualcrossing_forecast_empty_dates(weather_service):
    """Test fetch with empty dates list"""
    data = await weather_service._fetch_visualcrossing_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        dates=[]
    )
    assert data == []

@pytest.mark.asyncio
async def test_fetch_visualcrossing_forecast_api_failure(weather_service):
    """Test fetch when API returns an error"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("API connection failed"))
    weather_service.http_client = mock_client

    dates = [date(2026, 2, 20)]
    data = await weather_service._fetch_visualcrossing_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    assert data == []

@pytest.mark.asyncio
async def test_fetch_visualcrossing_forecast_malformed_json(weather_service):
    """Test fetch when API returns malformed JSON"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"unexpected": "format"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client

    dates = [date(2026, 2, 20)]
    data = await weather_service._fetch_visualcrossing_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    assert data == []
