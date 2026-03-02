from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WeatherStation(BaseModel):
    """
    Weather Station model representing a physical or virtual weather station.
    """
    __tablename__ = "weather_stations"

    name = Column(String, nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True) # Optional link to Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    provider = Column(String, nullable=True) # e.g. "OpenWeatherMap"
    status = Column(String, default="active")
    additional_info = Column(JSON, nullable=True)

    # Relationships
    location = relationship("Location")
    forecasts = relationship("ForecastData", back_populates="station", cascade="all, delete-orphan")
    historical_records = relationship("HistoricalRecord", back_populates="station", cascade="all, delete-orphan")
    alerts = relationship("AlertSubscription", back_populates="station", cascade="all, delete-orphan")

class ForecastData(BaseModel):
    """
    Forecast Data model storing weather predictions.
    """
    __tablename__ = "weather_forecasts"

    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True) # Date the forecast is for
    generated_at = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, nullable=False) # The forecast payload
    source = Column(String, nullable=True)

    station = relationship("WeatherStation", back_populates="forecasts")

class HistoricalRecord(BaseModel):
    """
    Historical Weather Record model storing past weather data.
    """
    __tablename__ = "weather_historical"

    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    precipitation = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    data = Column(JSON, nullable=True) # Extra data

    station = relationship("WeatherStation", back_populates="historical_records")

class ClimateZone(BaseModel):
    """
    Climate Zone model representing geographic zones.
    """
    __tablename__ = "climate_zones"

    name = Column(String, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=True)
    additional_info = Column(JSON, nullable=True)

class AlertSubscription(BaseModel):
    """
    Alert Subscription model for user notifications.
    """
    __tablename__ = "weather_alert_subscriptions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True) # Subscribe to location
    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=True) # Or station
    alert_type = Column(String, nullable=False)
    threshold = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    location = relationship("Location")
    station = relationship("WeatherStation", back_populates="alerts")
