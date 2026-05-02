"""
IoT Sensor Payload Schemas

Defines the structure for incoming sensor data from various sources (Generic HTTP, LoRaWAN/TTN).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SensorReading(BaseModel):
    """
    Individual sensor reading within a payload.
    """
    sensor_type: str = Field(..., description="Type of sensor (e.g., 'temperature', 'humidity', 'soil_moisture')")
    value: float = Field(..., description="The measured value")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., 'C', '%', 'hPa')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for this specific reading")

    model_config = ConfigDict(populate_by_name=True)


class GenericIngestionPayload(BaseModel):
    """
    Standardized payload for generic HTTP ingestion.
    """
    device_id: str = Field(..., description="Unique device identifier (e.g., UUID, MAC address)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time of measurement (UTC)")
    readings: List[SensorReading] = Field(..., description="List of sensor readings")
    location: Optional[Dict[str, float]] = Field(None, description="Optional location (lat, lon, alt)")
    battery_level: Optional[float] = Field(None, description="Device battery level (0-100)")
    signal_strength: Optional[float] = Field(None, description="Signal strength (RSSI/SNR)")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("readings")
    @classmethod
    def validate_readings_not_empty(cls, v: List[SensorReading]) -> List[SensorReading]:
        if not v:
            raise ValueError("readings list cannot be empty")
        return v


# TTN V3 Uplink Structures
class TTNEndDeviceIds(BaseModel):
    device_id: str
    application_ids: Dict[str, str]
    dev_eui: Optional[str] = None
    join_eui: Optional[str] = None
    dev_addr: Optional[str] = None

class TTNUplinkMessage(BaseModel):
    f_port: int
    f_cnt: int
    frm_payload: Optional[str] = None # Base64 encoded payload
    decoded_payload: Optional[Dict[str, Any]] = None
    rx_metadata: Optional[List[Dict[str, Any]]] = None
    settings: Optional[Dict[str, Any]] = None
    received_at: datetime

    # Optional fields often present in TTN v3
    session_key_id: Optional[str] = None
    network_ids: Optional[Dict[str, str]] = None


class TTNUplinkPayload(BaseModel):
    """
    The Things Network (TTN) v3 Uplink Payload.
    """
    end_device_ids: TTNEndDeviceIds
    correlation_ids: List[str]
    received_at: datetime
    uplink_message: TTNUplinkMessage

    model_config = ConfigDict(extra="ignore") # Ignore extra fields sent by TTN we don't need
