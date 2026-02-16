"""
Field Scanner Models
Scan results, plot analysis, and detection results
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class FieldScan(BaseModel):
    """A single field scan result with AI detection outputs"""

    __tablename__ = "field_scans"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    plot_id = Column(String(100), nullable=True, index=True)
    study_id = Column(String(100), nullable=True, index=True)
    crop = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    results = Column(JSON, nullable=False, default=list)
    thumbnail_url = Column(String(500), nullable=True)
    notes = Column(String(2000), nullable=True)
    weather = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=True)

    # Relationships
    organization = relationship("Organization", backref="field_scans")
