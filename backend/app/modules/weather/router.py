
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db

from . import services
from .schemas import (
    AlertSubscription,
    AlertSubscriptionCreate,
    AlertSubscriptionUpdate,
    ClimateZone,
    ClimateZoneCreate,
    ForecastData,
    ForecastDataCreate,
    HistoricalRecord,
    HistoricalRecordCreate,
    WeatherStation,
    WeatherStationCreate,
    WeatherStationUpdate,
)


router = APIRouter(prefix="/weather", tags=["Weather Service"])

# ============ Weather Station ============

@router.get("/stations", response_model=list[WeatherStation])
async def list_weather_stations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    results, _ = await services.weather_station.get_multi(db, skip=skip, limit=limit)
    return results

@router.post("/stations", response_model=WeatherStation)
async def create_weather_station(
    station: WeatherStationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await services.weather_station.create(db, obj_in=station)

@router.get("/stations/{station_id}", response_model=WeatherStation)
async def get_weather_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    station = await services.weather_station.get(db, id=station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Weather station not found")
    return station

@router.put("/stations/{station_id}", response_model=WeatherStation)
async def update_weather_station(
    station_id: int,
    station_in: WeatherStationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    station = await services.weather_station.get(db, id=station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Weather station not found")
    return await services.weather_station.update(db, db_obj=station, obj_in=station_in)

@router.delete("/stations/{station_id}", response_model=WeatherStation)
async def delete_weather_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    station = await services.weather_station.get(db, id=station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Weather station not found")
    return await services.weather_station.remove(db, id=station_id)

# ============ Forecast Data ============

@router.get("/forecasts", response_model=list[ForecastData])
async def list_forecast_data(
    station_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    filters = {}
    if station_id:
        filters['station_id'] = station_id

    results, _ = await services.forecast_data.get_multi(db, skip=skip, limit=limit, filters=filters)
    return results

@router.post("/forecasts", response_model=ForecastData)
async def create_forecast_data(
    forecast: ForecastDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await services.forecast_data.create(db, obj_in=forecast)

@router.get("/forecasts/{forecast_id}", response_model=ForecastData)
async def get_forecast_data(
    forecast_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    forecast = await services.forecast_data.get(db, id=forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast data not found")
    return forecast

@router.delete("/forecasts/{forecast_id}", response_model=ForecastData)
async def delete_forecast_data(
    forecast_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    forecast = await services.forecast_data.get(db, id=forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast data not found")
    return await services.forecast_data.remove(db, id=forecast_id)

# ============ Historical Record ============

@router.get("/historical", response_model=list[HistoricalRecord])
async def list_historical_records(
    station_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    filters = {}
    if station_id:
        filters['station_id'] = station_id

    results, _ = await services.historical_record.get_multi(db, skip=skip, limit=limit, filters=filters)
    return results

@router.post("/historical", response_model=HistoricalRecord)
async def create_historical_record(
    record: HistoricalRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await services.historical_record.create(db, obj_in=record)

@router.get("/historical/{record_id}", response_model=HistoricalRecord)
async def get_historical_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    record = await services.historical_record.get(db, id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Historical record not found")
    return record

@router.delete("/historical/{record_id}", response_model=HistoricalRecord)
async def delete_historical_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    record = await services.historical_record.get(db, id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Historical record not found")
    return await services.historical_record.remove(db, id=record_id)

# ============ Climate Zone ============

@router.get("/climate-zones", response_model=list[ClimateZone])
async def list_climate_zones(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    results, _ = await services.climate_zone.get_multi(db, skip=skip, limit=limit)
    return results

@router.post("/climate-zones", response_model=ClimateZone)
async def create_climate_zone(
    zone: ClimateZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await services.climate_zone.create(db, obj_in=zone)

@router.get("/climate-zones/{zone_id}", response_model=ClimateZone)
async def get_climate_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    zone = await services.climate_zone.get(db, id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Climate zone not found")
    return zone

@router.delete("/climate-zones/{zone_id}", response_model=ClimateZone)
async def delete_climate_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    zone = await services.climate_zone.get(db, id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Climate zone not found")
    return await services.climate_zone.remove(db, id=zone_id)

# ============ Alert Subscription ============

@router.get("/alerts/subscriptions", response_model=list[AlertSubscription])
async def list_alert_subscriptions(
    user_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    filters = {}
    if user_id:
        filters['user_id'] = user_id

    results, _ = await services.alert_subscription.get_multi(db, skip=skip, limit=limit, filters=filters)
    return results

@router.post("/alerts/subscriptions", response_model=AlertSubscription)
async def create_alert_subscription(
    subscription: AlertSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await services.alert_subscription.create(db, obj_in=subscription)

@router.get("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscription)
async def get_alert_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    subscription = await services.alert_subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Alert subscription not found")
    return subscription

@router.put("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscription)
async def update_alert_subscription(
    subscription_id: int,
    subscription_in: AlertSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    subscription = await services.alert_subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Alert subscription not found")
    return await services.alert_subscription.update(db, db_obj=subscription, obj_in=subscription_in)

@router.delete("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscription)
async def delete_alert_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    subscription = await services.alert_subscription.get(db, id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Alert subscription not found")
    return await services.alert_subscription.remove(db, id=subscription_id)
