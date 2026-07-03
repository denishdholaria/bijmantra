from app.crud.base import CRUDBase

from .models import AlertSubscription, ClimateZone, ForecastData, HistoricalRecord, WeatherStation
from .schemas import (
    AlertSubscriptionCreate,
    AlertSubscriptionUpdate,
    ClimateZoneCreate,
    ForecastDataCreate,
    HistoricalRecordCreate,
    WeatherStationCreate,
    WeatherStationUpdate,
)


class WeatherStationService(CRUDBase[WeatherStation, WeatherStationCreate, WeatherStationUpdate]):
    pass

class ForecastDataService(CRUDBase[ForecastData, ForecastDataCreate, ForecastDataCreate]):
    pass

class HistoricalRecordService(CRUDBase[HistoricalRecord, HistoricalRecordCreate, HistoricalRecordCreate]):
    pass

class ClimateZoneService(CRUDBase[ClimateZone, ClimateZoneCreate, ClimateZoneCreate]):
    pass

class AlertSubscriptionService(CRUDBase[AlertSubscription, AlertSubscriptionCreate, AlertSubscriptionUpdate]):
    pass

weather_station = WeatherStationService(WeatherStation)
forecast_data = ForecastDataService(ForecastData)
historical_record = HistoricalRecordService(HistoricalRecord)
climate_zone = ClimateZoneService(ClimateZone)
alert_subscription = AlertSubscriptionService(AlertSubscription)
