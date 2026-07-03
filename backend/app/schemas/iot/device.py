"""
IoT Device Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Base Schema
class IoTDeviceBase(BaseModel):
    name: str = Field(..., description="Human-readable name of the device")
    description: Optional[str] = None

    device_type: str = Field(..., description="Type of device (weather, soil, etc.)")
    connectivity: Optional[str] = None
    protocol: Optional[str] = None

    location_description: Optional[str] = None
    elevation: Optional[float] = None

    # BrAPI Integration
    field_id: Optional[int] = None
    environment_id: Optional[str] = None
    study_id: Optional[int] = None

    # Metadata
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None

    additional_info: Optional[Dict[str, Any]] = None


# Create Schema
class IoTDeviceCreate(IoTDeviceBase):
    device_db_id: str = Field(..., description="Unique device identifier (e.g. MAC address, UUID)")
    sensors: Optional[List[str]] = Field(default=[], description="List of sensor types to auto-register")


# Update Schema
class IoTDeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    device_type: Optional[str] = None
    connectivity: Optional[str] = None
    protocol: Optional[str] = None

    status: Optional[str] = None
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    firmware_version: Optional[str] = None

    location_description: Optional[str] = None
    elevation: Optional[float] = None

    field_id: Optional[int] = None
    environment_id: Optional[str] = None
    study_id: Optional[int] = None

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    calibration_date: Optional[datetime] = None

    additional_info: Optional[Dict[str, Any]] = None


# Response Schema
class IoTDeviceResponse(IoTDeviceBase):
    id: int
    device_db_id: str
    status: str
    battery_level: Optional[int]
    signal_strength: Optional[int]
    firmware_version: Optional[str]
    last_seen: Optional[datetime]
    installation_date: Optional[datetime]
    calibration_date: Optional[datetime]

    organization_id: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# List Response
class IoTDeviceListResponse(BaseModel):
    total: int
    items: List[IoTDeviceResponse]
