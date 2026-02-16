"""
Fertilizer Recommendation Model

Generates nutrient application recommendations based on soil tests and yield targets.

Scientific Basis:
    Nutrient requirement = (Target yield × Crop uptake) - Soil supply
    
    Where:
    - Target yield: Expected yield in kg/ha or t/ha
    - Crop uptake: Nutrient removed per unit yield (crop-specific)
    - Soil supply: Available nutrients from soil test

Common Crop Nutrient Uptake (kg nutrient per ton grain):
    - Wheat: N=25, P2O5=10, K2O=20
    - Rice: N=20, P2O5=10, K2O=25
    - Corn: N=25, P2O5=10, K2O=20
    - Soybean: N=80 (fixed), P2O5=15, K2O=35

Fertilizer Use Efficiency (typical):
    - Nitrogen: 40-60%
    - Phosphorus: 15-25%
    - Potassium: 50-70%

Reference: FAO Fertilizer and Plant Nutrition Bulletin
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
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class FertilizerRecommendation(BaseModel):
    """
    Fertilizer recommendation based on soil test and yield target.
    
    This model stores calculated fertilizer recommendations for a specific
    field and crop, including macronutrients (N, P, K) and micronutrients
    (S, Zn), application timing, and cost estimates.
    
    Attributes:
        id: Primary key
        organization_id: Multi-tenant isolation (RLS)
        soil_test_id: Reference to soil test results used for calculation
        field_id: Reference to field receiving recommendation
        crop_name: Target crop for recommendation
        target_yield: Expected yield goal
        yield_unit: Unit for yield (e.g., "t/ha", "kg/ha", "bu/ac")
        n_kg_ha: Nitrogen recommendation (kg/ha)
        p_kg_ha: Phosphorus (P2O5) recommendation (kg/ha)
        k_kg_ha: Potassium (K2O) recommendation (kg/ha)
        s_kg_ha: Sulfur recommendation (kg/ha)
        zn_kg_ha: Zinc recommendation (kg/ha)
        application_timing: JSON with timing details for split applications
        estimated_cost: Total estimated fertilizer cost
        currency: Currency code (e.g., "USD", "INR", "EUR")
        recommendation_date: Date recommendation was generated
        valid_until: Expiration date for recommendation
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "fertilizer_recommendations"

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # References (nullable for flexibility)
    soil_test_id = Column(Integer, nullable=True, index=True)
    field_id = Column(Integer, nullable=True, index=True)

    # Crop and yield target
    crop_name = Column(String(100), nullable=False, index=True)
    target_yield = Column(
        Float,
        nullable=False,
        comment="Target yield value"
    )
    yield_unit = Column(
        String(20),
        nullable=False,
        default="t/ha",
        comment="Unit for yield (t/ha, kg/ha, bu/ac)"
    )

    # Macronutrient recommendations (kg/ha)
    n_kg_ha = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Nitrogen recommendation in kg/ha"
    )
    p_kg_ha = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Phosphorus (P2O5) recommendation in kg/ha"
    )
    k_kg_ha = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Potassium (K2O) recommendation in kg/ha"
    )

    # Secondary and micronutrient recommendations (kg/ha)
    s_kg_ha = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="Sulfur recommendation in kg/ha"
    )
    zn_kg_ha = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="Zinc recommendation in kg/ha"
    )

    # Application timing (JSON for flexibility)
    application_timing = Column(
        JSONB,
        nullable=True,
        comment="Split application schedule with timing and amounts"
    )
    # Example application_timing structure:
    # {
    #     "splits": [
    #         {"timing": "basal", "n_percent": 50, "p_percent": 100, "k_percent": 50},
    #         {"timing": "tillering", "n_percent": 25, "p_percent": 0, "k_percent": 25},
    #         {"timing": "panicle_initiation", "n_percent": 25, "p_percent": 0, "k_percent": 25}
    #     ],
    #     "notes": "Apply basal dose at transplanting"
    # }

    # Cost estimation
    estimated_cost = Column(
        Float,
        nullable=True,
        comment="Total estimated fertilizer cost"
    )
    currency = Column(
        String(3),
        nullable=True,
        default="USD",
        comment="ISO 4217 currency code"
    )

    # Validity period
    recommendation_date = Column(
        Date,
        nullable=False,
        default=date.today,
        comment="Date recommendation was generated"
    )
    valid_until = Column(
        Date,
        nullable=True,
        comment="Recommendation expiration date"
    )

    # Additional notes
    notes = Column(
        Text,
        nullable=True,
        comment="Additional recommendations or caveats"
    )

    # Relationships
    organization = relationship("Organization")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_fert_rec_org_field", "organization_id", "field_id"),
        Index("ix_fert_rec_org_crop", "organization_id", "crop_name"),
        Index("ix_fert_rec_org_date", "organization_id", "recommendation_date"),
        CheckConstraint("target_yield > 0", name="ck_target_yield_positive"),
        CheckConstraint("n_kg_ha >= 0", name="ck_n_non_negative"),
        CheckConstraint("p_kg_ha >= 0", name="ck_p_non_negative"),
        CheckConstraint("k_kg_ha >= 0", name="ck_k_non_negative"),
    )

    def __repr__(self) -> str:
        return (
            f"<FertilizerRecommendation(id={self.id}, crop={self.crop_name}, "
            f"N={self.n_kg_ha}, P={self.p_kg_ha}, K={self.k_kg_ha} kg/ha)>"
        )

    @property
    def total_npk_kg_ha(self) -> float:
        """Total NPK recommendation in kg/ha."""
        return self.n_kg_ha + self.p_kg_ha + self.k_kg_ha
