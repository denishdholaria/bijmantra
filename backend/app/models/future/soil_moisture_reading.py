"""
Soil Moisture Reading Model

Stores soil moisture sensor readings for irrigation management.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SoilMoistureReading(BaseModel):
    """
    Represents a single soil moisture reading from a sensor.
    
    Used for irrigation scheduling and water balance calculations.
    """
    __tablename__ = "soil_moisture_readings"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)

    # Core measurement data
    reading_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    depth_cm = Column(Float, nullable=False)
    volumetric_water_content = Column(Float, nullable=False)  # VWC as decimal (0-1)
    soil_temperature_c = Column(Float, nullable=True)
    electrical_conductivity = Column(Float, nullable=True)  # dS/m

    # Sensor metadata
    sensor_type = Column(String(50), default="soil_moisture")
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    # Device status
    battery_level = Column(Integer, nullable=True)  # Percentage
    signal_strength = Column(Integer, nullable=True)  # dBm or percentage

    # Relationships
    organization = relationship("Organization")
    device = relationship("IoTDevice")
    field = relationship("Location")

    __table_args__ = (
        Index('ix_soil_moisture_org_device_timestamp', 'organization_id', 'device_id', 'reading_timestamp'),
    )

    def __repr__(self):
        return f"<SoilMoistureReading(device_id={self.device_id}, vwc={self.volumetric_water_content})>"
