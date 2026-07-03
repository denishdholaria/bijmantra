"""
Warehouse Management Models
Storage locations, capacity tracking, and environmental monitoring
"""

import enum

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class StorageType(enum.StrEnum):
    COLD = "cold"
    AMBIENT = "ambient"
    CONTROLLED = "controlled"
    CRYO = "cryo"


class LocationStatus(enum.StrEnum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class StorageLocation(BaseModel):
    """Physical storage location within a warehouse"""

    __tablename__ = "storage_locations"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    storage_type = Column(String(20), nullable=False, default=StorageType.AMBIENT.value)
    capacity_kg = Column(Float, nullable=False, default=0)
    used_kg = Column(Float, nullable=False, default=0)
    current_temperature = Column(Float, nullable=True)
    current_humidity = Column(Float, nullable=True)
    target_temperature = Column(Float, nullable=True)
    target_humidity = Column(Float, nullable=True)
    lot_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default=LocationStatus.NORMAL.value)
    description = Column(String(1000), nullable=True)

    # Relationships
    organization = relationship("Organization", backref="storage_locations")
