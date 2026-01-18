"""
Crop Calendar Module Models
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CropCalendar(BaseModel):
    """Crop Calendar model for tracking planting and harvest dates"""

    __tablename__ = "crop_calendars"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crop_name = Column(String(255), nullable=False, index=True)
    planting_date = Column(Date)
    harvest_date = Column(Date)

    # Relationships
    organization = relationship("Organization")
