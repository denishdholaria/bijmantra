"""
Unit tests for GDD Weather Sync Endpoints

Tests the weather data synchronization endpoints that integrate with
the weather_integration_service for real weather data fetching.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.services.weather_integration_service import (
    WeatherDataResponse,
    TemperatureData,
    WeatherProvider,
    DataQuality
)


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    # For testing, we'll mock the authentication
    # In real tests, you'd generate a valid JWT token
    return {"Authorization": "Bearer mock_token"}


@pytest.fixture
def mock_weather_response():
    """Create a mock weather data response"""
    temp_data = [
        TemperatureData(
            date=date(2026, 1, 15),
            temp_max=25.0,
            temp_min=15.0,
            temp_avg=20.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95,
            is_forecast=False,
            is_interpolated=False,
            outlier_detected=False,
            precipitation=0.0,
            humidity=65.0,
            wind_speed=10.0
        ),
        TemperatureData(
            date=date(2026, 1, 16),
            temp_max=26.0,
            temp_min=16.0,
            temp_avg=21.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.EXCELLENT,
            confidence=0.95,
            is_forecast=False,
            is_interpolated=False,
            outlier_detected=False,
            precipitation=2.5,
            humidity=70.0,
            wind_speed=12.0
        )
    ]
    
    return WeatherDataResponse(
        location_id="test-location-1",
        data=temp_data,
        provider_used=WeatherProvider.OPENWEATHERMAP,
        cache_hit_rate=0.5,
        data_completeness=1.0,
        quality_score=0.95,
        confidence={
            "type": "qualitative",
            "value": 0.95,
            "basis": "data_quality_validation"
        },
        validity_conditions=[
            "temperature_data_within_climatological_norms",
            "data_completeness_100percent"
        ],
        provenance={
            "data_sources": ["openweathermap"],
            "models_used": ["weather_integration_v1.0"],
            "timestamp": "2026-01-17T10:00:00Z",
            "cached_records": 1,
            "fetched_records": 1
        }
    )


class TestWeatherSyncEndpoint:
    """Tests for POST /api/v2/gdd/weather/sync endpoint"""
    
    @pytest.mark.asyncio
    async def test_sync_weather_data_success(
        self,
        async_client: AsyncClient,
        mock_weather_response,
        auth_headers
    ):
        """Test successful weather data sync"""
        # Mock authentication
        from app.models.core import User
        mock_user = User(
            id=1,
            email="test@bijmantra.org",
            organization_id=1,
            is_active=True
        )
        
        with patch(
            'app.api.deps.get_current_active_user',
            return_value=mock_user
        ):
            with patch(
                'app.services.weather_integration_service.weather_integration_service.get_temperature_data',
                new_callable=AsyncMock
            ) as mock_get_temp:
                mock_get_temp.return_value = mock_weather_response
                
                response = await async_client.post(
                    "/api/v2/gdd/weather/sync",
                    params={
                        "location_id": "test-location-1",
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                        "start_date": "2026-01-15",
                        "end_date": "2026-01-16",
                        "include_forecast": False
                    },
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Check data structure
                assert "data" in data
                assert "metadata" in data
                
                # Check data content
                assert data["data"]["location_id"] == "test-location-1"
                assert data["data"]["records_fetched"] == 2
                assert data["data"]["provider_used"] == "openweathermap"
                assert data["data"]["quality_score"] == 0.95
                
                # Check temperature data
                assert len(data["data"]["temperature_data"]) == 2
                temp_record = data["data"]["temperature_data"][0]
                assert temp_record["date"] == "2026-01-15"
                assert temp_record["temp_max"] == 25.0
                assert temp_record["temp_min"] == 15.0
                assert temp_record["quality"] == "excellent"
                
                # Check metadata
                assert "confidence" in data["metadata"]
                assert "validity_conditions" in data["metadata"]
                assert "provenance" in data["metadata"]
    
    @pytest.mark.asyncio
    async def test_sync_weather_data_invalid_date_range(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync with invalid date range (start > end)"""
        response = await async_client.post(
            "/api/v2/gdd/weather/sync",
            params={
                "location_id": "test-location-1",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "start_date": "2026-01-20",
                "end_date": "2026-01-10",
                "include_forecast": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_sync_weather_data_excessive_date_range(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync with date range exceeding 365 days"""
        response = await async_client.post(
            "/api/v2/gdd/weather/sync",
            params={
                "location_id": "test-location-1",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "start_date": "2025-01-01",
                "end_date": "2026-12-31",
                "include_forecast": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Date range cannot exceed 365 days" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_sync_weather_data_invalid_coordinates(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync with invalid latitude/longitude"""
        # Invalid latitude (> 90)
        response = await async_client.post(
            "/api/v2/gdd/weather/sync",
            params={
                "location_id": "test-location-1",
                "latitude": 95.0,
                "longitude": -74.0060,
                "start_date": "2026-01-15",
                "end_date": "2026-01-16"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_sync_weather_data_with_forecast(
        self,
        async_client: AsyncClient,
        mock_weather_response,
        auth_headers
    ):
        """Test sync with forecast data included"""
        # Add forecast data to mock response
        forecast_data = TemperatureData(
            date=date(2026, 1, 17),
            temp_max=24.0,
            temp_min=14.0,
            temp_avg=19.0,
            source=WeatherProvider.OPENWEATHERMAP,
            quality=DataQuality.GOOD,
            confidence=0.85,
            is_forecast=True,
            is_interpolated=False,
            outlier_detected=False
        )
        mock_weather_response.data.append(forecast_data)
        
        with patch(
            'app.services.weather_integration_service.weather_integration_service.get_temperature_data',
            new_callable=AsyncMock
        ) as mock_get_temp:
            mock_get_temp.return_value = mock_weather_response
            
            response = await async_client.post(
                "/api/v2/gdd/weather/sync",
                params={
                    "location_id": "test-location-1",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-17",
                    "include_forecast": True
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that forecast data is included
            assert data["data"]["records_fetched"] == 3
            forecast_record = data["data"]["temperature_data"][2]
            assert forecast_record["is_forecast"] is True


class TestBatchWeatherSyncEndpoint:
    """Tests for POST /api/v2/gdd/weather/sync/batch endpoint"""
    
    @pytest.mark.asyncio
    async def test_batch_sync_success(
        self,
        async_client: AsyncClient,
        mock_weather_response,
        auth_headers
    ):
        """Test successful batch weather sync"""
        with patch(
            'app.services.weather_integration_service.weather_integration_service.get_temperature_data',
            new_callable=AsyncMock
        ) as mock_get_temp:
            mock_get_temp.return_value = mock_weather_response
            
            batch_requests = [
                {
                    "location_id": "field-1",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-16"
                },
                {
                    "location_id": "field-2",
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-16"
                }
            ]
            
            response = await async_client.post(
                "/api/v2/gdd/weather/sync/batch",
                json=batch_requests,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check batch results
            assert data["data"]["total_requests"] == 2
            assert data["data"]["successful"] == 2
            assert data["data"]["failed"] == 0
            
            # Check individual results
            results = data["data"]["results"]
            assert len(results) == 2
            assert all(r["status"] == "success" for r in results)
            assert results[0]["location_id"] == "field-1"
            assert results[1]["location_id"] == "field-2"
    
    @pytest.mark.asyncio
    async def test_batch_sync_partial_failure(
        self,
        async_client: AsyncClient,
        mock_weather_response,
        auth_headers
    ):
        """Test batch sync with some failures"""
        async def mock_get_temp_side_effect(request, db=None):
            if request.location_id == "field-2":
                raise Exception("API rate limit exceeded")
            return mock_weather_response
        
        with patch(
            'app.services.weather_integration_service.weather_integration_service.get_temperature_data',
            new_callable=AsyncMock
        ) as mock_get_temp:
            mock_get_temp.side_effect = mock_get_temp_side_effect
            
            batch_requests = [
                {
                    "location_id": "field-1",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-16"
                },
                {
                    "location_id": "field-2",
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-16"
                }
            ]
            
            response = await async_client.post(
                "/api/v2/gdd/weather/sync/batch",
                json=batch_requests,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check batch results
            assert data["data"]["total_requests"] == 2
            assert data["data"]["successful"] == 1
            assert data["data"]["failed"] == 1
            
            # Check individual results
            results = data["data"]["results"]
            assert results[0]["status"] == "success"
            assert results[1]["status"] == "failed"
            assert "error" in results[1]
    
    @pytest.mark.asyncio
    async def test_batch_sync_missing_fields(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test batch sync with missing required fields"""
        batch_requests = [
            {
                "location_id": "field-1",
                # Missing latitude, longitude, dates
            }
        ]
        
        response = await async_client.post(
            "/api/v2/gdd/weather/sync/batch",
            json=batch_requests,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle gracefully
        assert data["data"]["failed"] == 1
        assert "Missing required fields" in data["data"]["results"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_batch_sync_excessive_batch_size(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test batch sync with too many requests"""
        batch_requests = [
            {
                "location_id": f"field-{i}",
                "latitude": 40.0,
                "longitude": -74.0,
                "start_date": "2026-01-15",
                "end_date": "2026-01-16"
            }
            for i in range(51)  # Exceeds limit of 50
        ]
        
        response = await async_client.post(
            "/api/v2/gdd/weather/sync/batch",
            json=batch_requests,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Batch size cannot exceed 50" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_batch_sync_empty_request(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test batch sync with empty request list"""
        response = await async_client.post(
            "/api/v2/gdd/weather/sync/batch",
            json=[],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "No sync requests provided" in response.json()["detail"]


class TestWeatherSyncStatusEndpoint:
    """Tests for GET /api/v2/gdd/weather/sync/status endpoint"""
    
    @pytest.mark.asyncio
    async def test_sync_status_with_cached_data(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync status check with cached data available"""
        # Mock Redis client with cached data
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"date": "2026-01-15"}')
        
        with patch(
            'app.services.weather_integration_service.weather_integration_service.redis_client',
            mock_redis
        ):
            with patch(
                'app.services.weather_integration_service.weather_integration_service._init_redis',
                new_callable=AsyncMock
            ):
                response = await async_client.get(
                    "/api/v2/gdd/weather/sync/status",
                    params={"location_id": "test-location-1"},
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Check status data
                assert data["data"]["location_id"] == "test-location-1"
                assert "sync_status" in data["data"]
                assert "cached_records_last_30_days" in data["data"]
                assert "data_coverage_percentage" in data["data"]
                assert "recommendation" in data["data"]
                
                # Check metadata
                assert "confidence" in data["metadata"]
                assert "validity_conditions" in data["metadata"]
    
    @pytest.mark.asyncio
    async def test_sync_status_no_cached_data(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync status check with no cached data"""
        # Mock Redis client with no cached data
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch(
            'app.services.weather_integration_service.weather_integration_service.redis_client',
            mock_redis
        ):
            with patch(
                'app.services.weather_integration_service.weather_integration_service._init_redis',
                new_callable=AsyncMock
            ):
                response = await async_client.get(
                    "/api/v2/gdd/weather/sync/status",
                    params={"location_id": "test-location-1"},
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should indicate poor coverage
                assert data["data"]["cached_records_last_30_days"] == 0
                assert data["data"]["data_coverage_percentage"] == 0.0
                assert data["data"]["sync_status"] == "poor"
                assert "sync recommended" in data["data"]["recommendation"].lower()
    
    @pytest.mark.asyncio
    async def test_sync_status_redis_unavailable(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test sync status check when Redis is unavailable"""
        with patch(
            'app.services.weather_integration_service.weather_integration_service.redis_client',
            None
        ):
            with patch(
                'app.services.weather_integration_service.weather_integration_service._init_redis',
                new_callable=AsyncMock
            ):
                response = await async_client.get(
                    "/api/v2/gdd/weather/sync/status",
                    params={"location_id": "test-location-1"},
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should indicate cache unavailable
                assert data["data"]["cache_available"] is False
                assert "redis_unavailable" in data["metadata"]["validity_conditions"]


class TestWeatherSyncIntegration:
    """Integration tests for weather sync endpoints"""
    
    @pytest.mark.asyncio
    async def test_sync_then_check_status(
        self,
        async_client: AsyncClient,
        mock_weather_response,
        auth_headers
    ):
        """Test syncing data then checking status"""
        with patch(
            'app.services.weather_integration_service.weather_integration_service.get_temperature_data',
            new_callable=AsyncMock
        ) as mock_get_temp:
            mock_get_temp.return_value = mock_weather_response
            
            # First, sync weather data
            sync_response = await async_client.post(
                "/api/v2/gdd/weather/sync",
                params={
                    "location_id": "test-location-1",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "start_date": "2026-01-15",
                    "end_date": "2026-01-16"
                },
                headers=auth_headers
            )
            
            assert sync_response.status_code == 200
            
            # Then check sync status
            # Note: In real scenario, data would be cached
            # For this test, we're just verifying the endpoint flow
            status_response = await async_client.get(
                "/api/v2/gdd/weather/sync/status",
                params={"location_id": "test-location-1"},
                headers=auth_headers
            )
            
            assert status_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(
        self,
        async_client: AsyncClient
    ):
        """Test that endpoints require authentication"""
        # Test sync endpoint
        response = await async_client.post(
            "/api/v2/gdd/weather/sync",
            params={
                "location_id": "test-location-1",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "start_date": "2026-01-15",
                "end_date": "2026-01-16"
            }
        )
        assert response.status_code == 401
        
        # Test batch sync endpoint
        response = await async_client.post(
            "/api/v2/gdd/weather/sync/batch",
            json=[]
        )
        assert response.status_code == 401
        
        # Test status endpoint
        response = await async_client.get(
            "/api/v2/gdd/weather/sync/status",
            params={"location_id": "test-location-1"}
        )
        assert response.status_code == 401
