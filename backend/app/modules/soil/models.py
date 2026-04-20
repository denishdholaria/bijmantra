from sqlalchemy import Column, Date, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class NutrientTest(Base):
    __tablename__ = "soil_nutrient_tests"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)  # ForeignKey("fields.id") - simplified for module independence
    sample_date = Column(Date, nullable=False)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PhysicalProperties(Base):
    __tablename__ = "soil_physical_properties"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    texture_class = Column(String, nullable=True)
    bulk_density = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MicrobialActivity(Base):
    __tablename__ = "soil_microbial_activity"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    respiration_rate = Column(Float, nullable=True) # mg CO2-C/kg soil/hr
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AmendmentLog(Base):
    __tablename__ = "soil_amendment_logs"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    amendment_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SoilMap(Base):
    __tablename__ = "soil_maps"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    map_type = Column(String, nullable=False) # e.g., "pH", "EC", "OM"
    image_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
