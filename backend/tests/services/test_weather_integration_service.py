"""
Unit tests for Weather Integration Service

Tests cover:
- Temperature data fetching with multiple providers
- Caching mechanisms and cache hit rates
- Rate limiting enforcement
- Data quality validation and outlier detection
- Fallback mechanisms when APIs fail
- BijMantra API contract compliance (uncertainty metadata)
"""

import pytest
from datetime import date, datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.weather_integration_service import (
    WeatherIntegrationService,
    WeatherDataRequest,
    WeatherDataResponse,
    TemperatureData,
    WeatherProvider,
    DataQuality
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def weather_service():
    """Create weather integration service instance"""
    service = WeatherIntegrationService()
    return service


@pytest.fixture
def sample_request():
    """Sample weather data request"""
    return WeatherDataRequest(
        location_id="LOC-001",
        latitude=40.7128,
        longitude=-74.0060,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 7),
        include_forecast=False
    )


@pytest.fixture
def sample_temperature_data():
    """Sample temperature data"""
    return [
        TemperatureData(
            date=date(2026, 1, 1),
            temp_max=15.5,
            temp_min=5.2,
            temp_avg=10.3,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95,
            is_forecast=False
        ),
        TemperatureData(
            date=date(2026, 1, 2),
            temp_max=16.8,
            temp_min=6.1,
            temp_avg=11.4,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95,
            is_forecast=False
        )
    ]


# ============================================
# CACHE MANAGEMENT TESTS
# ============================================

@pytest.mark.asyncio
async def test_cache_data_and_retrieval(weather_service, sample_temperature_data):
    """Test caching temperature data and retrieving it"""
    location_id = "LOC-001"
    dates = [d.date for d in sample_temperature_data]
    
    # Mock Redis client
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Cache data
    await weather_service._cache_data(location_id, sample_temperature_data)
    
    # Verify setex was called for each data point
    assert redis_mock.setex.call_count == len(sample_temperature_data)


@pytest.mark.asyncio
async def test_get_cached_data_hit(weather_service):
    """Test retrieving cached data successfully"""
    location_id = "LOC-001"
    dates = [date(2026, 1, 1), date(2026, 1, 2)]
    
    # Mock Redis with cached data
    cached_temp = TemperatureData(
        date=date(2026, 1, 1),
        temp_max=15.5,
        temp_min=5.2,
        source=WeatherProvider.CACHED,
        quality=DataQuality.GOOD,
        confidence=0.9
    )
    
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=cached_temp.model_dump_json())
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Get cached data
    cached_data, missing_dates = await weather_service._get_cached_data(
        location_id, [dates[0]]
    )
    
    assert len(cached_data) == 1
    assert cached_data[0].date == date(2026, 1, 1)
    assert len(missing_dates) == 0


@pytest.mark.asyncio
async def test_get_cached_data_miss(weather_service):
    """Test cache miss returns missing dates"""
    location_id = "LOC-001"
    dates = [date(2026, 1, 1), date(2026, 1, 2)]
    
    # Mock Redis with no cached data
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Get cached data
    cached_data, missing_dates = await weather_service._get_cached_data(
        location_id, dates
    )
    
    assert len(cached_data) == 0
    assert len(missing_dates) == 2
    assert missing_dates == dates


# ============================================
# RATE LIMITING TESTS
# ============================================

@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit(weather_service):
    """Test rate limiting allows calls within limit"""
    provider = "openweathermap"
    
    # Should allow first call
    allowed = await weather_service._check_rate_limit(provider)
    assert allowed is True
    
    # Should allow subsequent calls within limit
    for _ in range(10):
        allowed = await weather_service._check_rate_limit(provider)
        assert allowed is True


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(weather_service):
    """Test rate limiting blocks calls over limit"""
    provider = "openweathermap"
    
    # Fill up rate limit (60 calls/hour)
    for _ in range(60):
        await weather_service._check_rate_limit(provider)
    
    # Next call should be blocked
    allowed = await weather_service._check_rate_limit(provider)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limit_cleans_old_timestamps(weather_service):
    """Test rate limiting cleans up old timestamps"""
    provider = "visualcrossing"
    
    # Add old timestamp (>1 hour ago)
    old_time = datetime.now(UTC) - timedelta(hours=2)
    weather_service._rate_limits[provider] = [old_time]
    
    # Check rate limit (should clean old timestamp)
    allowed = await weather_service._check_rate_limit(provider)
    assert allowed is True
    assert len(weather_service._rate_limits[provider]) == 1  # Only new timestamp


# ============================================
# DATA VALIDATION TESTS
# ============================================

def test_validate_data_quality_normal(weather_service, sample_temperature_data):
    """Test data validation with normal temperature data"""
    validated = weather_service._validate_data_quality(sample_temperature_data)
    
    assert len(validated) == len(sample_temperature_data)
    assert all(not d.outlier_detected for d in validated)


def test_validate_data_quality_outlier_range(weather_service):
    """Test data validation detects out-of-range temperatures"""
    data = [
        TemperatureData(
            date=date(2026, 1, 1),
            temp_max=75.0,  # Unrealistic
            temp_min=5.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95
        )
    ]
    
    validated = weather_service._validate_data_quality(data)
    
    assert validated[0].outlier_detected is True
    assert validated[0].quality == DataQuality.POOR


def test_validate_data_quality_tmax_less_than_tmin(weather_service):
    """Test data validation detects Tmax < Tmin"""
    data = [
        TemperatureData(
            date=date(2026, 1, 1),
            temp_max=5.0,  # Less than Tmin
            temp_min=15.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95
        )
    ]
    
    validated = weather_service._validate_data_quality(data)
    
    assert validated[0].outlier_detected is True
    assert validated[0].quality == DataQuality.POOR


def test_validate_data_quality_large_day_to_day_change(weather_service):
    """Test data validation detects large day-to-day temperature changes"""
    data = [
        TemperatureData(
            date=date(2026, 1, 1),
            temp_max=15.0,
            temp_min=5.0,
            temp_avg=10.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95
        ),
        TemperatureData(
            date=date(2026, 1, 2),
            temp_max=45.0,  # 35°C jump
            temp_min=35.0,
            temp_avg=40.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95
        )
    ]
    
    validated = weather_service._validate_data_quality(data)
    
    assert validated[1].outlier_detected is True
    assert validated[1].quality == DataQuality.FAIR


def test_calculate_quality_score(weather_service):
    """Test quality score calculation"""
    data = [
        TemperatureData(
            date=date(2026, 1, 1),
            temp_max=15.0,
            temp_min=5.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95
        ),
        TemperatureData(
            date=date(2026, 1, 2),
            temp_max=16.0,
            temp_min=6.0,
            source=WeatherProvider.VISUAL_CROSSING,
            quality=DataQuality.GOOD,
            confidence=0.85
        ),
        TemperatureData(
            date=date(2026, 1, 3),
            temp_max=14.0,
            temp_min=4.0,
            source=WeatherProvider.CACHED,
            quality=DataQuality.FAIR,
            confidence=0.65
        )
    ]
    
    score = weather_service._calculate_quality_score(data)
    
    # Score should be average of (1.0 + 0.85 + 0.65) / 3 = 0.833
    assert 0.8 <= score <= 0.9


# ============================================
# API INTEGRATION TESTS (MOCKED)
# ============================================

@pytest.mark.asyncio
async def test_fetch_openweathermap_forecast(weather_service):
    """Test fetching forecast from OpenWeatherMap"""
    # Mock HTTP client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "daily": [
            {
                "dt": int(datetime(2026, 1, 1, tzinfo=UTC).timestamp()),
                "temp": {"max": 15.5, "min": 5.2, "day": 10.3},
                "humidity": 65,
                "wind_speed": 5.5,
                "rain": 2.5,
                "snow": 0
            },
            {
                "dt": int(datetime(2026, 1, 2, tzinfo=UTC).timestamp()),
                "temp": {"max": 16.8, "min": 6.1, "day": 11.4},
                "humidity": 70,
                "wind_speed": 4.2,
                "rain": 0,
                "snow": 0
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client
    weather_service.openweather_key = "test_key"
    
    # Fetch forecast
    data = await weather_service._fetch_openweathermap_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        days=2
    )
    
    assert len(data) == 2
    assert data[0].date == date(2026, 1, 1)
    assert data[0].temp_max == 15.5
    assert data[0].temp_min == 5.2
    assert data[0].is_forecast is True
    assert data[0].source == WeatherProvider.OPENWEATHERMAP


@pytest.mark.asyncio
async def test_fetch_visualcrossing_historical(weather_service):
    """Test fetching historical data from Visual Crossing"""
    # Mock HTTP client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "days": [
            {
                "datetime": "2026-01-01",
                "tempmax": 15.5,
                "tempmin": 5.2,
                "temp": 10.3,
                "precip": 2.5,
                "humidity": 65,
                "windspeed": 15.5
            },
            {
                "datetime": "2026-01-02",
                "tempmax": 16.8,
                "tempmin": 6.1,
                "temp": 11.4,
                "precip": 0,
                "humidity": 70,
                "windspeed": 12.2
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client
    weather_service.visualcrossing_key = "test_key"
    
    # Fetch historical data
    dates = [date(2026, 1, 1), date(2026, 1, 2)]
    data = await weather_service._fetch_visualcrossing_historical(
        latitude=40.7128,
        longitude=-74.0060,
        dates=dates
    )
    
    assert len(data) == 2
    assert data[0].date == date(2026, 1, 1)
    assert data[0].temp_max == 15.5
    assert data[0].temp_min == 5.2
    assert data[0].is_forecast is False
    assert data[0].source == WeatherProvider.VISUAL_CROSSING
    assert data[0].quality == DataQuality.EXCELLENT


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_temperature_data_with_cache(weather_service, sample_request):
    """Test getting temperature data with cache hits"""
    # Mock Redis with cached data
    cached_temp = TemperatureData(
        date=date(2026, 1, 1),
        temp_max=15.5,
        temp_min=5.2,
        source=WeatherProvider.CACHED,
        quality=DataQuality.GOOD,
        confidence=0.9
    )
    
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=cached_temp.model_dump_json())
    redis_mock.setex = AsyncMock()
    redis_mock.ping = AsyncMock()
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Get temperature data
    response = await weather_service.get_temperature_data(sample_request)
    
    assert isinstance(response, WeatherDataResponse)
    assert response.location_id == sample_request.location_id
    assert response.cache_hit_rate > 0
    assert 0 <= response.quality_score <= 1
    
    # Verify BijMantra API contract compliance
    assert "confidence" in response.model_dump()
    assert "validity_conditions" in response.model_dump()
    assert "provenance" in response.model_dump()


@pytest.mark.asyncio
async def test_get_temperature_data_api_fallback(weather_service, sample_request):
    """Test API fallback when primary fails"""
    # Mock Redis with no cache
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    redis_mock.ping = AsyncMock()
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Mock OpenWeatherMap failure
    weather_service.openweather_key = ""
    
    # Mock Visual Crossing success
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "days": [
            {
                "datetime": "2026-01-01",
                "tempmax": 15.5,
                "tempmin": 5.2,
                "temp": 10.3,
                "precip": 0,
                "humidity": 65,
                "windspeed": 15.5
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    weather_service.http_client = mock_client
    weather_service.visualcrossing_key = "test_key"
    
    # Get temperature data (should fall back to Visual Crossing)
    response = await weather_service.get_temperature_data(sample_request)
    
    assert isinstance(response, WeatherDataResponse)
    assert response.provider_used in [WeatherProvider.VISUAL_CROSSING, WeatherProvider.CACHED]


# ============================================
# UTILITY TESTS
# ============================================

def test_generate_date_range(weather_service):
    """Test date range generation"""
    start = date(2026, 1, 1)
    end = date(2026, 1, 5)
    
    dates = weather_service._generate_date_range(start, end)
    
    assert len(dates) == 5
    assert dates[0] == start
    assert dates[-1] == end
    assert all(isinstance(d, date) for d in dates)


def test_generate_date_range_single_day(weather_service):
    """Test date range generation for single day"""
    start = date(2026, 1, 1)
    end = date(2026, 1, 1)
    
    dates = weather_service._generate_date_range(start, end)
    
    assert len(dates) == 1
    assert dates[0] == start


# ============================================
# ERROR HANDLING TESTS
# ============================================

@pytest.mark.asyncio
async def test_cache_failure_graceful_degradation(weather_service, sample_temperature_data):
    """Test graceful degradation when cache fails"""
    location_id = "LOC-001"
    
    # Mock Redis failure
    redis_mock = AsyncMock()
    redis_mock.setex = AsyncMock(side_effect=Exception("Redis connection failed"))
    weather_service.redis_client = redis_mock
    weather_service._redis_initialized = True
    
    # Should not raise exception
    await weather_service._cache_data(location_id, sample_temperature_data)


@pytest.mark.asyncio
async def test_api_failure_returns_empty(weather_service):
    """Test API failure returns empty list"""
    # Mock HTTP client failure
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("API connection failed"))
    weather_service.http_client = mock_client
    weather_service.openweather_key = "test_key"
    
    # Should return empty list, not raise exception
    data = await weather_service._fetch_openweathermap_forecast(
        latitude=40.7128,
        longitude=-74.0060,
        days=7
    )
    
    assert data == []
