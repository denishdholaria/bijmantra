"""
Biosimulation Models
Crop Growth Models, Phenology, and Yield Simulation
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class CropModel(Base):
    """
    Defines species-specific or variety-specific growth parameters.
    Example: "Maize-Medium-Maturity"
    """
    __tablename__ = "crop_models"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, unique=True)
    crop_name = Column(String(100), nullable=False) # e.g. "Maize"
    description = Column(String(500))
    
    # Phenology Parameters (Thermal Time)
    base_temp = Column(Float, default=10.0, comment="Base temperature (C)")
    opt_temp = Column(Float, default=30.0, comment="Optimal temperature (C)")
    max_temp = Column(Float, default=40.0, comment="Maximum temperature (C)")
    
    gdd_emergence = Column(Float, comment="GDD required for emergence")
    gdd_flowering = Column(Float, comment="GDD required for flowering")
    gdd_maturity = Column(Float, comment="GDD required for physiological maturity")
    
    # Growth Parameters
    rue = Column(Float, default=1.5, comment="Radiation Use Efficiency (g/MJ)")
    harvest_index = Column(Float, default=0.5, comment="Harvest Index (Yield/Biomass)")
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")


class SimulationRun(Base):
    """
    Results of a specific simulation run.
    """
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Context
    model_id = Column(Integer, ForeignKey("crop_models.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    
    # Results
    predicted_flowering_date = Column(DateTime)
    predicted_maturity_date = Column(DateTime)
    predicted_yield = Column(Float, comment="Estimated yield (kg/ha)")
    predicted_biomass = Column(Float, comment="Total biomass (kg/ha)")
    
    # Status
    status = Column(String(50), default="COMPLETED") # PENDING, COMPLETED, FAILED
    logs = Column(JSON, comment="Execution logs or warnings")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
    crop_model = relationship("CropModel")
    location = relationship("Location")
