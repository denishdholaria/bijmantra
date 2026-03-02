"""
Unit tests for Historical Weather Integration Service

Tests cover:
- Fetching historical weather data using OpenWeatherMap 'day_summary' endpoint.
- Handling successful responses.
- Handling API errors (401, 403, 500).
- Handling rate limits.
"""

import pytest
from datetime import date, datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock
from app.services.weather_integration_service import (
    WeatherIntegrationService,
    TemperatureData,
    WeatherProvider,
    DataQuality
)

@pytest.fixture
def weather_service():
    """Create weather integration service instance"""
    service = WeatherIntegrationService()
    service.openweather_key = "test_key"
    return service

@pytest.mark.asyncio
async def test_fetch_openweathermap_historical_success(weather_service):
    """Test fetching historical data from OpenWeatherMap successfully"""
    # Mock HTTP client
    mock_response = MagicMock()
    # Mock response for a single day summary
    # Based on OWM One Call 3.0 day_summary structure
    mock_response.json.return_value = {
        "lat": 40.7128,
        "lon": -74.0060,
        "date": "2023-01-01",
        "temperature": {
            "min": 5.2,
            "max": 15.5,
            "afternoon": 12.0,
            "night": 6.0,
            "evening": 10.0,
            "morning": 7.0
        },
        "precipitation": {
            "total": 2.5
        },
        "humidity": {
            "afternoon": 65.0
        },
        "wind": {
            "max": {
                "speed": 5.5,
                "direction": 180.0
            }
        }
    }
    mock_response.raise_for_status = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client

    # Fetch historical data
    dates = [date(2023, 1, 1)]
    data = await weather_service._fetch_openweathermap_historical(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    assert len(data) == 1
    d = data[0]
    assert d.date == date(2023, 1, 1)
    assert d.temp_max == 15.5
    assert d.temp_min == 5.2
    assert d.temp_avg == 12.0  # Afternoon temp
    assert d.precipitation == 2.5
    assert d.humidity == 65.0
    assert d.wind_speed == 5.5 * 3.6  # m/s to km/h conversion
    assert d.source == WeatherProvider.OPENWEATHERMAP
    assert d.quality == DataQuality.EXCELLENT
    assert d.is_forecast is False

@pytest.mark.asyncio
async def test_fetch_openweathermap_historical_unauthorized(weather_service):
    """Test handling of 401 Unauthorized (e.g. invalid key or no subscription)"""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client

    # Fetch historical data
    dates = [date(2023, 1, 1), date(2023, 1, 2)]
    data = await weather_service._fetch_openweathermap_historical(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    # Should return empty list and break loop
    assert len(data) == 0
    # Should only attempt once if unauthorized
    assert mock_client.get.call_count == 1

@pytest.mark.asyncio
async def test_fetch_openweathermap_historical_rate_limit(weather_service):
    """Test rate limiting prevents API calls"""
    # Fill up rate limit
    weather_service._rate_limits["openweathermap"] = [
        datetime.now(UTC) for _ in range(60)
    ]

    mock_client = AsyncMock()
    weather_service.http_client = mock_client

    dates = [date(2023, 1, 1)]
    data = await weather_service._fetch_openweathermap_historical(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    # Should be empty because rate limit reached
    assert len(data) == 0
    assert mock_client.get.call_count == 0

@pytest.mark.asyncio
async def test_fetch_openweathermap_historical_partial_failure(weather_service):
    """Test partial failure (one day fails, next succeeds)"""
    # First call fails (500), second succeeds
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 500
    mock_response_fail.raise_for_status.side_effect = Exception("500 Server Error")

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "lat": 40.7128, "lon": -74.0060, "date": "2023-01-02",
        "temperature": {"min": 6.0, "max": 16.0, "afternoon": 13.0},
        "precipitation": {"total": 0.0},
        "humidity": {"afternoon": 70.0},
        "wind": {"max": {"speed": 4.0}}
    }
    mock_response_success.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
    weather_service.http_client = mock_client

    dates = [date(2023, 1, 1), date(2023, 1, 2)]
    data = await weather_service._fetch_openweathermap_historical(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )

    # Should have data for second date only
    assert len(data) == 1
    assert data[0].date == date(2023, 1, 2)
    # Should attempt both calls
    assert mock_client.get.call_count == 2
