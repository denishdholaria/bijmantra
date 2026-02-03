from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from app.models.base import BaseModel
from datetime import datetime, timezone

class BarcodeScan(BaseModel):
    """Barcode scan history"""
    __tablename__ = "barcode_scans"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    barcode_value = Column(String(255), nullable=False, index=True)
    scanned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    scanned_by = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    found = Column(Boolean, default=False)

    # Entity details (denormalized for history preservation)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)
    entity_name = Column(String(255), nullable=True)
