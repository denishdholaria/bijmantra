import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.weather.models import WeatherStation, ForecastData
from datetime import date, datetime

@pytest.mark.asyncio
async def test_weather_station_create(async_db_session: AsyncSession):
    station = WeatherStation(
        name="Test Station",
        latitude=10.0,
        longitude=20.0,
        provider="TestProvider"
    )
    async_db_session.add(station)
    await async_db_session.commit()
    await async_db_session.refresh(station)

    assert station.id is not None
    assert station.name == "Test Station"
    assert station.latitude == 10.0

@pytest.mark.asyncio
async def test_forecast_data_create(async_db_session: AsyncSession):
    station = WeatherStation(
        name="Forecast Station",
        latitude=10.0,
        longitude=20.0
    )
    async_db_session.add(station)
    await async_db_session.commit()
    await async_db_session.refresh(station)

    forecast = ForecastData(
        station_id=station.id,
        forecast_date=date(2026, 1, 1),
        data={"temp": 25}
    )
    async_db_session.add(forecast)
    await async_db_session.commit()
    await async_db_session.refresh(forecast)

    assert forecast.id is not None
    assert forecast.station_id == station.id
    assert forecast.data["temp"] == 25
