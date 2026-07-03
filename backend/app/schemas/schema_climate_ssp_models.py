"""
Climate SSP Models Schema

Defines Pydantic models for Shared Socioeconomic Pathways (SSP) climate data.
This schema supports climate projection analysis and risk assessment.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SSPScenario(str, Enum):
    """
    Shared Socioeconomic Pathways (SSP) Scenarios with Radiative Forcing targets.
    """
    SSP1_19 = "SSP1-1.9"  # Sustainability (Taking the Green Road)
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"  # Middle of the Road
    SSP3_70 = "SSP3-7.0"  # Regional Rivalry
    SSP4_34 = "SSP4-3.4"  # Inequality
    SSP4_60 = "SSP4-6.0"
    SSP5_85 = "SSP5-8.5"  # Fossil-fueled Development
    HISTORICAL = "historical"


class ClimateVariable(str, Enum):
    """Standard climate variables (CMIP6)."""
    TAS = "tas"  # Near-Surface Air Temperature (Kelvin)
    TASMIN = "tasmin"  # Daily Minimum Near-Surface Air Temperature
    TASMAX = "tasmax"  # Daily Maximum Near-Surface Air Temperature
    PR = "pr"  # Precipitation (kg m-2 s-1)
    HURS = "hurs"  # Near-Surface Relative Humidity (%)
    RSDS = "rsds"  # Surface Downwelling Shortwave Radiation (W m-2)
    SFC_WIND = "sfcWind"  # Near-Surface Wind Speed (m s-1)
    CO2 = "co2"  # Atmospheric CO2 Concentration (ppm)
    CH4 = "ch4"  # Atmospheric CH4 Concentration (ppb)
    POP = "pop"  # Population
    GDP = "gdp"  # Gross Domestic Product


class TemporalResolution(str, Enum):
    """Temporal resolution of the data."""
    DAILY = "daily"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    DECADAL = "decadal"


class SSPModelMetadata(BaseModel):
    """Metadata for a Global Circulation Model (GCM) or Integrated Assessment Model (IAM)."""

    model_name: str = Field(..., description="Name of the climate model (e.g., 'UKESM1-0-LL')")
    institution: str = Field(..., description="Institution that developed the model")
    variant_label: str = Field("r1i1p1f1", description="Ensemble member variant label")
    grid_label: str = Field("gn", description="Grid label (e.g., 'gn' for native grid)")
    nominal_resolution: str | None = Field(None, description="Nominal resolution (e.g., '100 km')")

    model_config = ConfigDict(frozen=True)


class SSPDataPoint(BaseModel):
    """A single data point in a climate projection series."""

    year: int = Field(..., ge=1850, le=2500, description="Year of the data point")
    value: float = Field(..., description="Projected value")
    unit: str = Field(..., description="Unit of measurement (e.g., 'K', 'mm/day')")
    uncertainty_range: tuple[float, float] | None = Field(
        None, description="Optional uncertainty range (min, max)"
    )

    @field_validator("uncertainty_range")
    @classmethod
    def validate_range(cls, v: tuple[float, float] | None) -> tuple[float, float] | None:
        if v is not None:
            min_val, max_val = v
            if min_val > max_val:
                raise ValueError("Uncertainty range min must be <= max")
        return v


class SSPProjection(BaseModel):
    """
    Climate projection series for a specific scenario, variable, and location.
    """

    scenario: SSPScenario = Field(..., description="SSP Scenario")
    variable: ClimateVariable = Field(..., description="Climate Variable")
    location_id: str | None = Field(None, description="Location identifier if applicable")
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    model_metadata: SSPModelMetadata = Field(..., description="Source model metadata")
    temporal_resolution: TemporalResolution = Field(..., description="Time step of the data")

    data: list[SSPDataPoint] = Field(..., description="Time series data")

    baseline_year: int = Field(2015, description="Reference year for projections")

    source_citation: str | None = Field(None, description="Citation for the data source")

    @property
    def min_year(self) -> int:
        if not self.data:
            return 0
        return min(d.year for d in self.data)

    @property
    def max_year(self) -> int:
        if not self.data:
            return 0
        return max(d.year for d in self.data)


class ClimateRiskAssessment(BaseModel):
    """Assessment of climate risk based on SSP projections."""

    scenario: SSPScenario
    risk_level: Annotated[int, Field(ge=1, le=5)] = Field(..., description="Risk level 1 (Low) to 5 (Critical)")
    description: str = Field(..., description="Description of the risk")
    impact_sectors: list[str] = Field(default_factory=list, description="Sectors impacted (e.g., 'Agriculture', 'Water')")
    confidence: str = Field("medium", description="Confidence level (low, medium, high)")
