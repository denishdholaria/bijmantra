"""
Water Balance Model
"""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WaterBalance(BaseModel):
    """
    Represents daily water balance data for a specific field.
    """
    __tablename__ = "water_balances"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    balance_date = Column(Date, nullable=False, index=True)
    precipitation_mm = Column(Float, nullable=False)
    irrigation_mm = Column(Float, nullable=False)
    et_actual_mm = Column(Float, nullable=False)
    runoff_mm = Column(Float, nullable=False)
    deep_percolation_mm = Column(Float, nullable=False)
    soil_water_content_mm = Column(Float, nullable=False)
    available_water_mm = Column(Float, nullable=False)
    deficit_mm = Column(Float, nullable=False)
    surplus_mm = Column(Float, nullable=False)
    crop_name = Column(String(255))
    growth_stage = Column(String(100))

    # Relationships
    organization = relationship("Organization")
    field = relationship("Field")
