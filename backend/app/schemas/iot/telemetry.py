"""
IoT Telemetry Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Base Schema
class TelemetryBase(BaseModel):
    value: float = Field(..., description="Sensor reading value")
    raw_value: Optional[float] = Field(None, description="Raw sensor reading value")

    quality: Optional[str] = Field("good", description="Data quality (good, suspect, bad)")
    quality_code: Optional[int] = None

    additional_info: Optional[Dict[str, Any]] = None

# Create Schema
class TelemetryCreate(TelemetryBase):
    device_db_id: str = Field(..., description="Device identifier")
    sensor_code: str = Field(..., description="Sensor type code (e.g. 'temp', 'humidity')")
    timestamp: Optional[datetime] = Field(None, description="Measurement timestamp")

# Response Schema
class TelemetryResponse(TelemetryBase):
    timestamp: datetime
    device_id: int
    sensor_id: int

    model_config = ConfigDict(from_attributes=True)

# List Response
class TelemetryListResponse(BaseModel):
    total: int
    items: List[TelemetryResponse]
