"""
Field Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import BaseModel

class Field(BaseModel):
    """
    Represents a physical field.
    """
    __tablename__ = "fields"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    location_id = Column(Integer, ForeignKey("locations.id"))
    area_hectares = Column(Float)
    geometry = Column(Geometry('POLYGON', srid=4326))

    # Relationships
    organization = relationship("Organization")
    location = relationship("Location")
