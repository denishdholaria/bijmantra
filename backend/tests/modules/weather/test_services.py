import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.weather import services
from app.modules.weather.schemas import WeatherStationCreate, ForecastDataCreate
from datetime import date

@pytest.mark.asyncio
async def test_weather_station_service(async_db_session: AsyncSession):
    station_in = WeatherStationCreate(
        name="Service Station",
        latitude=30.0,
        longitude=40.0,
        provider="ServiceTest"
    )
    station = await services.weather_station.create(async_db_session, obj_in=station_in)
    assert station.id is not None
    assert station.name == "Service Station"

    fetched = await services.weather_station.get(async_db_session, id=station.id)
    assert fetched.name == "Service Station"

@pytest.mark.asyncio
async def test_forecast_data_service(async_db_session: AsyncSession):
    station_in = WeatherStationCreate(
        name="Service Forecast Station",
        latitude=30.0,
        longitude=40.0
    )
    station = await services.weather_station.create(async_db_session, obj_in=station_in)

    forecast_in = ForecastDataCreate(
        station_id=station.id,
        forecast_date=date(2026, 2, 1),
        data={"humidity": 80}
    )
    forecast = await services.forecast_data.create(async_db_session, obj_in=forecast_in)
    assert forecast.id is not None
    assert forecast.data["humidity"] == 80
