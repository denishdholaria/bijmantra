from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ============= Weather Station Schemas =============

class WeatherStationBase(BaseModel):
    name: str
    location_id: int | None = None
    latitude: float
    longitude: float
    elevation: float | None = None
    provider: str | None = None
    status: str | None = "active"
    additional_info: dict[str, Any] | None = None

class WeatherStationCreate(WeatherStationBase):
    pass

class WeatherStationUpdate(BaseModel):
    name: str | None = None
    location_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation: float | None = None
    provider: str | None = None
    status: str | None = None
    additional_info: dict[str, Any] | None = None

class WeatherStation(WeatherStationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============= Forecast Data Schemas =============

class ForecastDataBase(BaseModel):
    station_id: int
    forecast_date: date
    data: dict[str, Any]
    source: str | None = None

class ForecastDataCreate(ForecastDataBase):
    pass

class ForecastData(ForecastDataBase):
    id: int
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============= Historical Record Schemas =============

class HistoricalRecordBase(BaseModel):
    station_id: int
    date: date
    temperature_max: float | None = None
    temperature_min: float | None = None
    precipitation: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    data: dict[str, Any] | None = None

class HistoricalRecordCreate(HistoricalRecordBase):
    pass

class HistoricalRecord(HistoricalRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============= Climate Zone Schemas =============

class ClimateZoneBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    additional_info: dict[str, Any] | None = None

class ClimateZoneCreate(ClimateZoneBase):
    pass

class ClimateZone(ClimateZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============= Alert Subscription Schemas =============

class AlertSubscriptionBase(BaseModel):
    user_id: int
    location_id: int | None = None
    station_id: int | None = None
    alert_type: str
    threshold: dict[str, Any]
    is_active: bool | None = True

class AlertSubscriptionCreate(AlertSubscriptionBase):
    pass

class AlertSubscriptionUpdate(BaseModel):
    location_id: int | None = None
    station_id: int | None = None
    alert_type: str | None = None
    threshold: dict[str, Any] | None = None
    is_active: bool | None = None

class AlertSubscription(AlertSubscriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
