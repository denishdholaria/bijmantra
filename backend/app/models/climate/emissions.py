"""
Emissions Tracking Models

Tracks agricultural emissions for carbon footprint analysis.

Scientific Basis:
    Agricultural Emissions Sources:
        - Fertilizer production and application: 1-5 kg CO2e/kg N
        - Fuel combustion: 2.7 kg CO2e/L diesel
        - Irrigation pumping: 0.5-1.5 kg CO2e/kWh
        - N2O from soil: 1-3% of applied N
    
    Carbon Intensity:
        CI (kg CO2e/kg yield) = Total Emissions / Total Yield
        
    Typical ranges:
        - Rice: 2-4 kg CO2e/kg grain
        - Wheat: 0.4-0.8 kg CO2e/kg grain
        - Maize: 0.3-0.6 kg CO2e/kg grain
"""

import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class EmissionCategory(str, enum.Enum):
    """Category of emission source"""
    FERTILIZER = "fertilizer"
    FUEL = "fuel"
    IRRIGATION = "irrigation"
    PESTICIDE = "pesticide"
    MACHINERY = "machinery"
    TRANSPORT = "transport"
    SOIL_N2O = "soil_n2o"
    OTHER = "other"


class EmissionSource(BaseModel):
    """
    Emission sources for trials/locations.
    
    Tracks specific emission-generating activities and inputs.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        location_id: Reference to field/location
        trial_id: Reference to trial (optional)
        study_id: Reference to study (optional)
        activity_date: Date of emission-generating activity
        category: Emission category
        source_name: Specific source (e.g., "Urea", "Diesel", "Electricity")
        quantity: Amount of input used
        unit: Unit of quantity (kg, L, kWh, etc.)
        emission_factor_id: Reference to emission factor
        co2e_emissions: Calculated CO2 equivalent emissions (kg)
        notes: Additional notes
    """

    __tablename__ = "emission_sources"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=True, index=True)

    activity_date = Column(Date, nullable=False, index=True)
    category = Column(Enum(EmissionCategory), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)

    # Input quantity
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)

    # Emissions calculation
    emission_factor_id = Column(Integer, ForeignKey("emission_factors.id"), nullable=True)
    co2e_emissions = Column(Float, nullable=False)  # kg CO2e

    # Notes
    notes = Column(String(1000), nullable=True)

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")
    trial = relationship("Trial")
    study = relationship("Study")
    emission_factor = relationship("EmissionFactor")


class EmissionFactor(BaseModel):
    """
    Emission factors database.
    
    Standard emission factors for converting inputs to CO2 equivalents.
    Based on IPCC guidelines and regional data.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        category: Emission category
        source_name: Specific source
        factor_value: Emission factor value
        unit: Unit of emission factor (kg CO2e/kg, kg CO2e/L, etc.)
        region: Geographic region (for regional factors)
        source_reference: Citation/reference for factor
        valid_from: Start date of validity
        valid_to: End date of validity
        metadata: Additional factor details (JSON)
    """

    __tablename__ = "emission_factors"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    category = Column(Enum(EmissionCategory), nullable=False, index=True)
    source_name = Column(String(255), nullable=False, index=True)

    # Factor value
    factor_value = Column(Float, nullable=False)
    unit = Column(String(100), nullable=False)  # kg CO2e/kg, kg CO2e/L, etc.

    # Geographic and temporal validity
    region = Column(String(100), nullable=True)
    source_reference = Column(String(500), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    # Additional metadata
    additional_data = Column(JSON, nullable=True)

    # Relationships
    organization = relationship("Organization")


class VarietyFootprint(BaseModel):
    """
    Carbon footprint per variety.
    
    Aggregated carbon intensity metrics for crop varieties.
    Enables comparison of varieties based on carbon efficiency.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        germplasm_id: Reference to variety/germplasm
        trial_id: Reference to trial
        study_id: Reference to study
        season_id: Reference to season
        location_id: Reference to location
        total_emissions: Total CO2e emissions (kg/ha)
        total_yield: Total yield (kg/ha or t/ha)
        carbon_intensity: Carbon intensity (kg CO2e/kg yield)
        emissions_by_category: Breakdown by category (JSON)
        measurement_date: Date of calculation
        notes: Additional notes
    """

    __tablename__ = "variety_footprints"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    # Emissions and yield
    total_emissions = Column(Float, nullable=False)  # kg CO2e/ha
    total_yield = Column(Float, nullable=False)  # kg/ha or t/ha
    carbon_intensity = Column(Float, nullable=False)  # kg CO2e/kg yield

    # Detailed breakdown
    emissions_by_category = Column(JSON, nullable=True)

    # Metadata
    measurement_date = Column(Date, nullable=False, index=True)
    notes = Column(String(1000), nullable=True)

    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm")
    trial = relationship("Trial")
    study = relationship("Study")
    season = relationship("Season")
    location = relationship("Location")
