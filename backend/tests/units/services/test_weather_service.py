import importlib

import pytest

weather_service_module = importlib.import_module(
    "app.modules.environment.services.weather_service"
)
from app.modules.environment.services.weather_service import (
    WeatherForecastUnavailableError,
    WeatherService,
)


@pytest.mark.asyncio
async def test_get_forecast_preserves_generated_fallback_by_default(monkeypatch):
    async def fail_forecast(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(weather_service_module.weather_client, "get_forecast", fail_forecast)

    service = WeatherService()

    forecast = await service.get_forecast(
        location_id="LOC-1",
        location_name="Ludhiana",
        days=3,
        crop="wheat",
        lat=30.9010,
        lon=75.8573,
    )

    assert forecast.location_id == "LOC-1"
    assert forecast.location_name == "Ludhiana"
    assert forecast.forecast_days == 3
    assert len(forecast.daily_forecast) == 3


@pytest.mark.asyncio
async def test_get_forecast_requires_coordinates_when_generated_fallback_disabled():
    service = WeatherService()

    with pytest.raises(
        WeatherForecastUnavailableError,
        match="location coordinates are required for live weather forecast",
    ):
        await service.get_forecast(
            location_id="LOC-1",
            location_name="Ludhiana",
            days=3,
            crop="wheat",
            allow_generated_fallback=False,
        )


@pytest.mark.asyncio
async def test_get_forecast_raises_when_live_provider_fails_and_generated_fallback_disabled(monkeypatch):
    async def fail_forecast(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(weather_service_module.weather_client, "get_forecast", fail_forecast)

    service = WeatherService()

    with pytest.raises(
        WeatherForecastUnavailableError,
        match="weather provider request failed",
    ):
        await service.get_forecast(
            location_id="LOC-1",
            location_name="Ludhiana",
            days=3,
            crop="wheat",
            lat=30.9010,
            lon=75.8573,
            allow_generated_fallback=False,
        )