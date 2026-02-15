"""
Environmental Physics Models
Growing Degree Days, Soil Moisture Profiles, and Photothermal Units
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class EnvironmentalUnit(Base):
    """
    Stores calculated environmental indices for a specific location and time period.
    Used for crop phenology tracking (GDD) and stress analysis.
    """
    __tablename__ = "environmental_units"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date_calculated = Column(DateTime, nullable=False)
    
    # Thermal Units
    gdd_accumulated = Column(Float, nullable=True, comment="Growing Degree Days (C)")
    ptu_accumulated = Column(Float, nullable=True, comment="Photothermal Units (C * hr)")
    
    # Moisture & Stress
    soil_moisture_index = Column(Float, nullable=True, comment="0-1 scale (1=saturation)")
    evapotranspiration = Column(Float, nullable=True, comment="ET0 in mm/day")
    
    # Metadata
    source_model = Column(String, default="standard_physics") # e.g. "standard_physics", "remote_sensing"
    
    # Relationships
    location = relationship("Location", back_populates="environmental_units")


class SoilProfile(Base):
    """
    Physical properties of the soil at a specific location.
    Parameters for the Van Genuchten equation for soil moisture.
    """
    __tablename__ = "soil_profiles"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Soil Texture & Classification
    sodium_category = Column(String, nullable=True) # e.g. "Sodic", "Non-Sodic"
    texture_class = Column(String, nullable=True)   # e.g. "Clay Loam"
    
    # Van Genuchten Parameters (Hydraulic Properties)
    theta_sat = Column(Float, nullable=False, comment="Saturated water content (cm3/cm3)")
    theta_res = Column(Float, nullable=False, comment="Residual water content (cm3/cm3)")
    alpha = Column(Float, nullable=False, comment="Inverse of air entry suction (1/cm)")
    n_param = Column(Float, nullable=False, comment="Pore size distribution index")
    ksat = Column(Float, nullable=True, comment="Saturated hydraulic conductivity (cm/day)")
    
    # Relationships
    location = relationship("Location", back_populates="soil_profile")
