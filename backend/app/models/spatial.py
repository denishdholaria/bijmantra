"""
Spatial Analysis Models
GIS Layers, Remote Sensing Data, and Spatial Indices
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.models.base import Base

class GISLayer(Base):
    """
    Metadata for a GIS data layer (Raster or Vector).
    Example: "Soil Types 2025", "Sentinel-2 NDVI Aug 2025"
    """
    __tablename__ = "gis_layers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False, index=True)
    layer_type = Column(String(50), nullable=False) # "raster", "vector"
    category = Column(String(50)) # "soil", "weather", "vegetation", "elevation"

    # improved storage for file paths or tile server URLs
    source_path = Column(String(512), comment="File path or URL")
    driver = Column(String(50), default="GTiff") # GDAL driver name
    crs = Column(String(50), default="EPSG:4326") # Coordinate Reference System

    # Raster specific metadata
    resolution = Column(Float, comment="Pixel size in meters or degrees")
    band_count = Column(Integer, default=1)
    band_names = Column(JSON, comment="List of band names e.g. ['Red', 'NIR']")

    # Metadata
    acquisition_date = Column(DateTime)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")


class RemoteSensingData(Base):
    """
    Computed vegetation indices or other remote sensing data for a specific location.
    Linked to a specific point or polygon (location).
    """
    __tablename__ = "remote_sensing_data"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)

    # Source
    source_layer_id = Column(Integer, ForeignKey("gis_layers.id"))
    acquisition_date = Column(DateTime, nullable=False)

    # Data
    metric_name = Column(String(50), nullable=False, index=True) # e.g. "NDVI", "EVI", "Elevation"
    value = Column(Float, nullable=False)

    # Context
    platform = Column(String(50)) # "Sentinel-2", "Landsat-8", "Drone"
    cloud_cover = Column(Float, comment="Cloud cover percentage")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")
    source_layer = relationship("GISLayer")
