"""
Growing Degree Day (GDD) Log Model

Tracks accumulated heat units for crop development prediction.

Scientific Formula:
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Where:
    - Tmax = Daily maximum temperature
    - Tmin = Daily minimum temperature  
    - Tbase = Base temperature (crop-specific threshold below which no growth occurs)

Common Base Temperatures:
    - Corn/Maize: 10°C (50°F)
    - Wheat: 0°C (32°F)
    - Rice: 10°C (50°F)
    - Soybean: 10°C (50°F)
    - Cotton: 15.5°C (60°F)

Cumulative GDD predicts growth stages:
    - Corn: ~125 GDD to emergence, ~1400 GDD to silking, ~2700 GDD to maturity
"""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class GrowingDegreeDayLog(BaseModel):
    """
    Daily Growing Degree Day (GDD) log for crop development tracking.
    
    GDD (also called heat units) measures accumulated warmth that drives
    crop development. This model stores daily and cumulative GDD values
    for field-level crop monitoring.
    
    Attributes:
        id: Primary key
        organization_id: Multi-tenant isolation (RLS)
        field_id: Reference to field/location where crop is planted
        crop_name: Crop being tracked (e.g., "Corn", "Wheat", "Rice")
        planting_date: Date crop was planted (GDD accumulation start)
        log_date: Date of this GDD record
        daily_gdd: GDD accumulated on this specific day
        cumulative_gdd: Total GDD accumulated since planting
        base_temperature: Crop-specific base temperature (°C)
        max_temperature: Daily maximum temperature (°C)
        min_temperature: Daily minimum temperature (°C)
        growth_stage: Predicted or observed growth stage
        created_at: Record creation timestamp
    """

    __tablename__ = "growing_degree_day_logs"

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Field reference (nullable for now as Field model may not exist)
    field_id = Column(Integer, nullable=True, index=True)

    # Crop identification
    crop_name = Column(String(100), nullable=False, index=True)

    # Date tracking
    planting_date = Column(Date, nullable=False)
    log_date = Column(Date, nullable=False, index=True)

    # GDD values
    daily_gdd = Column(
        Float,
        nullable=False,
        comment="GDD accumulated on this day (always >= 0)"
    )
    cumulative_gdd = Column(
        Float,
        nullable=False,
        comment="Total GDD since planting date"
    )

    # Temperature data
    base_temperature = Column(
        Float,
        nullable=False,
        default=10.0,
        comment="Base temperature in Celsius (crop-specific)"
    )
    max_temperature = Column(
        Float,
        nullable=True,
        comment="Daily maximum temperature in Celsius"
    )
    min_temperature = Column(
        Float,
        nullable=True,
        comment="Daily minimum temperature in Celsius"
    )

    # Growth stage prediction/observation
    growth_stage = Column(
        String(100),
        nullable=True,
        comment="Predicted or observed growth stage (e.g., 'V6', 'R1', 'Flowering')"
    )

    # Relationships
    organization = relationship("Organization")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_gdd_org_field_date", "organization_id", "field_id", "log_date"),
        Index("ix_gdd_org_crop_date", "organization_id", "crop_name", "log_date"),
        CheckConstraint("daily_gdd >= 0", name="ck_daily_gdd_non_negative"),
        CheckConstraint("cumulative_gdd >= 0", name="ck_cumulative_gdd_non_negative"),
        CheckConstraint("log_date >= planting_date", name="ck_log_date_after_planting"),
    )

    def __repr__(self) -> str:
        return (
            f"<GrowingDegreeDayLog(id={self.id}, crop={self.crop_name}, "
            f"date={self.log_date}, cumulative_gdd={self.cumulative_gdd})>"
        )
