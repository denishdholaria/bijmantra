"""
Yield Prediction Model

Stores crop yield predictions and their contributing factors.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Date, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class YieldPrediction(BaseModel):
    """
    Represents a yield prediction for a specific field and crop.
    
    Prediction methods include:
    - Statistical: Based on historical yield data
    - Process-based: Crop simulation models (DSSAT, APSIM)
    - ML-based: Machine learning from remote sensing + weather
    - Hybrid: Combination of above methods
    """
    __tablename__ = "yield_predictions"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=True, index=True)

    crop_name = Column(String(255), nullable=False, index=True)
    variety = Column(String(255), nullable=True)
    season = Column(String(50), nullable=False)  # e.g., "Kharif 2026", "Rabi 2025-26"

    # Prediction values
    predicted_yield = Column(Float, nullable=False)
    yield_unit = Column(String(50), default="t/ha")
    prediction_date = Column(Date, nullable=False)

    # Confidence interval
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    confidence_level = Column(Float, default=0.95)  # 95% CI

    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    prediction_method = Column(String(50))  # statistical, process, ml, hybrid

    # Contributing factors
    weather_factors = Column(JSON)  # Temperature, rainfall, etc.
    soil_factors = Column(JSON)  # Nutrients, moisture, etc.
    management_factors = Column(JSON)  # Irrigation, fertilizer, etc.

    # Actual yield (filled after harvest)
    actual_yield = Column(Float, nullable=True)
    prediction_error = Column(Float, nullable=True)  # Actual - Predicted

    notes = Column(Text)

    # Relationships
    organization = relationship("Organization")
    field = relationship("Location")
    trial = relationship("Trial")

    def __repr__(self):
        return f"<YieldPrediction(crop={self.crop_name}, predicted={self.predicted_yield} {self.yield_unit})>"
