from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.http_tracing import create_traced_async_client

# ============================================
# ENUMS & TYPES
# ============================================


class WeatherProvider(StrEnum):
    """Weather API providers"""
    OPENWEATHERMAP = "openweathermap"
    VISUAL_CROSSING = "visualcrossing"
    CACHED = "cached"
    INTERPOLATED = "interpolated"


class DataQuality(StrEnum):
    """Data quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


# ============================================
# SCHEMAS
# ============================================


class TemperatureData(BaseModel):
    """Daily temperature data for GDD calculation"""
    date: date
    temp_max: float
    temp_min: float
    temp_avg: float | None = None
    source: WeatherProvider
    quality: DataQuality = DataQuality.UNKNOWN
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    is_forecast: bool = False
    is_interpolated: bool = False
    outlier_detected: bool = False
    precipitation: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None


class WeatherDataRequest(BaseModel):
    """Request for weather data"""
    location_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_date: date
    end_date: date
    include_forecast: bool = False


class WeatherDataResponse(BaseModel):
    """Response with temperature data and metadata"""
    location_id: str
    data: list[TemperatureData]
    provider_used: WeatherProvider
    cache_hit_rate: float
    data_completeness: float
    quality_score: float
    confidence: dict[str, Any]
    validity_conditions: list[str]
    provenance: dict[str, Any]


class OpenMeteoClient:
    """
    Client for Open-Meteo API (Free, No-Key).
    Provides Historical Weather and Forecasts for agricultural analysis.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORY_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def get_forecast(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        """
        Fetch weather forecast.
        Variables: Max/Min Temp, Precipitation Sum, Et0.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "shortwave_radiation_sum",
                "soil_moisture_0_to_7cm_mean",
                "wind_speed_10m_max",
                "relative_humidity_2m_mean",
                "soil_temperature_0_to_7cm_mean",
                "vapor_pressure_deficit_max"
            ]),
            "timezone": "auto",
            "forecast_days": days
        }

        async with create_traced_async_client() as client:
            response = await client.get(self.FORECAST_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_historical_weather(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date
    ) -> dict[str, Any]:
        """
        Fetch historical weather for a date range.
        Useful for model calibration and retrospective analysis.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            # Debugging: Starting with basic variables only
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "shortwave_radiation_sum",
                "soil_moisture_0_to_7cm_mean",
                "soil_moisture_7_to_28cm_mean",
                # Extended Ag Variables via User Request:
                "wind_speed_10m_max",
                "relative_humidity_2m_mean",
                "soil_temperature_0_to_7cm_mean",
                "vapor_pressure_deficit_max"
            ]),
            "timezone": "auto"
        }

        async with create_traced_async_client() as client:
            response = await client.get(self.HISTORY_URL, params=params)
            response.raise_for_status()
            return response.json()

weather_client = OpenMeteoClient()


# Service instance for backward compatibility
class WeatherIntegrationService:
    """Wrapper service for weather integration"""
    
    def __init__(self):
        self.client = weather_client
    
    async def get_temperature_data(
        self,
        request: WeatherDataRequest
    ) -> WeatherDataResponse:
        """Get temperature data for a location and date range"""
        # Fetch historical data
        data = await self.client.get_historical_weather(
            lat=request.latitude,
            lon=request.longitude,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Parse response into TemperatureData objects
        temp_data = []
        if "daily" in data:
            dates = data["daily"].get("time", [])
            temp_max = data["daily"].get("temperature_2m_max", [])
            temp_min = data["daily"].get("temperature_2m_min", [])
            precip = data["daily"].get("precipitation_sum", [])
            
            for i, date_str in enumerate(dates):
                temp_data.append(TemperatureData(
                    date=date.fromisoformat(date_str),
                    temp_max=temp_max[i] if i < len(temp_max) else 0.0,
                    temp_min=temp_min[i] if i < len(temp_min) else 0.0,
                    temp_avg=(temp_max[i] + temp_min[i]) / 2 if i < len(temp_max) and i < len(temp_min) else None,
                    source=WeatherProvider.OPENWEATHERMAP,
                    quality=DataQuality.GOOD,
                    precipitation=precip[i] if i < len(precip) else None
                ))
        
        return WeatherDataResponse(
            location_id=request.location_id,
            data=temp_data,
            provider_used=WeatherProvider.OPENWEATHERMAP,
            cache_hit_rate=0.0,
            data_completeness=len(temp_data) / ((request.end_date - request.start_date).days + 1),
            quality_score=0.8,
            confidence={"level": "good"},
            validity_conditions=["historical_data"],
            provenance={"source": "open-meteo"}
        )

weather_integration_service = WeatherIntegrationService()
