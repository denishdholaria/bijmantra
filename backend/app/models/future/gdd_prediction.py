"""
Growing Degree Day (GDD) Prediction Model

Stores growth stage forecasts based on GDD accumulation patterns.
"""

from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class GDDPrediction(BaseModel):
    """
    Predicted growth stages based on GDD accumulation.

    Attributes:
        id: Primary key
        organization_id: Multi-tenant isolation
        field_id: Reference to field
        crop_name: Crop being tracked
        prediction_date: Date when this prediction was made
        target_stage: Growth stage being predicted (e.g., "Maturity", "Silking")
        predicted_date: Forecasted date for reaching the stage
        predicted_gdd: Estimated GDD accumulation at that date
        confidence: Confidence level of prediction (0.0 - 1.0)
        notes: Additional context or warnings
    """

    __tablename__ = "gdd_predictions"

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    field_id = Column(Integer, nullable=True, index=True)
    crop_name = Column(String(100), nullable=False, index=True)

    prediction_date = Column(Date, nullable=False, default=date.today)
    target_stage = Column(String(100), nullable=False)

    predicted_date = Column(Date, nullable=True)
    predicted_gdd = Column(Float, nullable=True)

    confidence = Column(Float, nullable=False, default=0.5)
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")

    # Indexes
    __table_args__ = (
        Index("ix_gdd_pred_org_field", "organization_id", "field_id"),
        Index("ix_gdd_pred_org_date", "organization_id", "prediction_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<GDDPrediction(id={self.id}, crop={self.crop_name}, "
            f"stage={self.target_stage}, date={self.predicted_date})>"
        )
