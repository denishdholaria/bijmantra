"""
Carbon Monitoring Models

Tracks soil and vegetation carbon stocks for climate mitigation.

Scientific Basis:
    Soil Organic Carbon (SOC):
        - Typical range: 0.5-5% by weight
        - Sequestration rate: 0.2-1.0 tonnes C/ha/year
        - Measurement depth: 0-30cm (standard) or 0-100cm (deep)
    
    Vegetation Carbon:
        - Biomass carbon = Dry biomass × 0.45 (carbon fraction)
        - Estimated from NDVI, LAI, or direct measurement
        - Includes above-ground and below-ground biomass
    
    Carbon Stock Calculation:
        Carbon Stock (t/ha) = SOC (%) × Bulk Density (g/cm³) × Depth (cm) × 100
"""

import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CarbonMeasurementType(str, enum.Enum):
    """Type of carbon measurement"""
    SOIL_ORGANIC = "soil_organic"
    VEGETATION_BIOMASS = "vegetation_biomass"
    TOTAL_ECOSYSTEM = "total_ecosystem"
    SATELLITE_ESTIMATED = "satellite_estimated"
    FIELD_MEASURED = "field_measured"


class CarbonStock(BaseModel):
    """
    Carbon Stock tracking for locations/fields.
    
    Represents the total carbon stored in soil and vegetation at a specific
    location and time. Used for baseline establishment and temporal monitoring.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        location_id: Reference to field/location
        measurement_date: Date of carbon stock assessment
        soil_carbon_stock: Soil organic carbon (tonnes C/ha)
        vegetation_carbon_stock: Above + below ground biomass carbon (tonnes C/ha)
        total_carbon_stock: Total ecosystem carbon (tonnes C/ha)
        measurement_depth_cm: Soil sampling depth (typically 30 or 100 cm)
        measurement_type: How carbon was measured
        confidence_level: Measurement confidence (0-1)
        gee_image_id: Google Earth Engine image ID (if satellite-based)
        metadata: Additional measurement details (JSON)
    """

    __tablename__ = "carbon_stocks"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    measurement_date = Column(Date, nullable=False, index=True)

    # Carbon stocks (tonnes C/ha)
    soil_carbon_stock = Column(Float, nullable=True)
    vegetation_carbon_stock = Column(Float, nullable=True)
    total_carbon_stock = Column(Float, nullable=False)

    # Measurement details
    measurement_depth_cm = Column(Integer, default=30)
    measurement_type = Column(Enum(CarbonMeasurementType), nullable=False)
    confidence_level = Column(Float, default=0.8)  # 0-1 scale

    # GEE integration
    gee_image_id = Column(String(255), nullable=True)

    # Additional metadata
    additional_data = Column(JSON, nullable=True)

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")
    measurements = relationship("CarbonMeasurement", back_populates="carbon_stock")


class CarbonMeasurement(BaseModel):
    """
    Individual carbon measurements (time series data).
    
    Stores detailed measurement data for carbon stock calculations.
    Multiple measurements can contribute to a single CarbonStock record.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        carbon_stock_id: Reference to parent carbon stock
        location_id: Reference to field/location
        measurement_date: Date of measurement
        measurement_type: Type of measurement
        carbon_value: Measured carbon value (units depend on type)
        unit: Measurement unit (%, t/ha, kg/m², etc.)
        depth_from_cm: Starting depth for soil samples
        depth_to_cm: Ending depth for soil samples
        bulk_density: Soil bulk density (g/cm³) for SOC calculations
        sample_id: Laboratory sample identifier
        method: Measurement method (Walkley-Black, dry combustion, etc.)
        notes: Additional notes
    """

    __tablename__ = "carbon_measurements"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    carbon_stock_id = Column(Integer, ForeignKey("carbon_stocks.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    measurement_date = Column(Date, nullable=False, index=True)
    measurement_type = Column(Enum(CarbonMeasurementType), nullable=False)

    # Measurement value
    carbon_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # %, t/ha, kg/m², etc.

    # Soil-specific fields
    depth_from_cm = Column(Integer, nullable=True)
    depth_to_cm = Column(Integer, nullable=True)
    bulk_density = Column(Float, nullable=True)  # g/cm³

    # Laboratory details
    sample_id = Column(String(100), nullable=True)
    method = Column(String(255), nullable=True)

    # Notes
    notes = Column(String(1000), nullable=True)

    # Relationships
    organization = relationship("Organization")
    carbon_stock = relationship("CarbonStock", back_populates="measurements")
    location = relationship("Location")
