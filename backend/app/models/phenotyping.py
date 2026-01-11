"""
BrAPI Phenotyping Module Models
Observation Variables (Traits), Observations, Observation Units, Samples, Images, Events
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, Date
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ObservationVariable(BaseModel):
    """BrAPI Observation Variable (Trait) - A measured characteristic"""
    
    __tablename__ = "observation_variables"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_variable_db_id = Column(String(255), unique=True, index=True)
    observation_variable_name = Column(String(255), nullable=False, index=True)
    common_crop_name = Column(String(100))
    default_value = Column(String(255))
    document_ids = Column(JSON)
    growth_stage = Column(String(100))
    institution = Column(String(255))
    language = Column(String(10))
    scientist = Column(String(255))
    status = Column(String(50))
    submission_timestamp = Column(String(50))
    synonyms = Column(JSON)
    
    # Trait info
    trait_db_id = Column(String(255), index=True)
    trait_name = Column(String(255))
    trait_description = Column(Text)
    trait_class = Column(String(100))
    
    # Method info
    method_db_id = Column(String(255))
    method_name = Column(String(255))
    method_description = Column(Text)
    method_class = Column(String(100))
    formula = Column(Text)
    
    # Scale info
    scale_db_id = Column(String(255))
    scale_name = Column(String(255))
    data_type = Column(String(50))
    decimal_places = Column(Integer)
    valid_values = Column(JSON)
    
    # Ontology
    ontology_db_id = Column(String(255))
    ontology_name = Column(String(255))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    observations = relationship("Observation", back_populates="observation_variable")


class ObservationUnit(BaseModel):
    """BrAPI Observation Unit - A unit being observed (plot, plant, etc.)"""
    
    __tablename__ = "observation_units"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), index=True)
    observation_unit_db_id = Column(String(255), unique=True, index=True)
    observation_unit_name = Column(String(255), nullable=False, index=True)
    observation_unit_pui = Column(String(255))
    cross_db_id = Column(String(255))
    seedlot_db_id = Column(String(255))
    observation_level = Column(String(50))
    observation_level_code = Column(String(50))
    observation_level_order = Column(Integer)
    
    # Position info
    position_coordinate_x = Column(String(50))
    position_coordinate_x_type = Column(String(50))
    position_coordinate_y = Column(String(50))
    position_coordinate_y_type = Column(String(50))
    entry_type = Column(String(50))
    geo_coordinates = Column(JSON)
    
    # Treatments
    treatments = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    study = relationship("Study")
    germplasm = relationship("Germplasm")
    observations = relationship("Observation", back_populates="observation_unit")
    samples = relationship("Sample", back_populates="observation_unit")
    images = relationship("Image", back_populates="observation_unit")


class Observation(BaseModel):
    """BrAPI Observation - A single data point measurement"""
    
    __tablename__ = "observations"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_unit_id = Column(Integer, ForeignKey("observation_units.id"), index=True)
    observation_variable_id = Column(Integer, ForeignKey("observation_variables.id"), index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), index=True)
    observation_db_id = Column(String(255), unique=True, index=True)
    collector = Column(String(255))
    observation_time_stamp = Column(String(50))
    season_db_id = Column(String(255))
    upload_timestamp = Column(String(50))
    value = Column(Text)
    
    # Geo coordinates
    geo_coordinates = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    observation_unit = relationship("ObservationUnit", back_populates="observations")
    observation_variable = relationship("ObservationVariable", back_populates="observations")
    study = relationship("Study")
    germplasm = relationship("Germplasm")


class Sample(BaseModel):
    """BrAPI Sample - A physical sample taken from an observation unit"""
    
    __tablename__ = "samples"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_unit_id = Column(Integer, ForeignKey("observation_units.id"), index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    sample_db_id = Column(String(255), unique=True, index=True)
    sample_name = Column(String(255), nullable=False, index=True)
    sample_pui = Column(String(255))
    sample_type = Column(String(100))
    sample_description = Column(Text)
    sample_barcode = Column(String(255))
    sample_group_db_id = Column(String(255))
    sample_timestamp = Column(String(50))
    taken_by = Column(String(255))
    plate_db_id = Column(String(255), index=True)
    plate_name = Column(String(255))
    plate_index = Column(Integer)
    well = Column(String(10))
    row = Column(String(10))
    column = Column(Integer)
    tissue_type = Column(String(100))
    concentration = Column(Float)
    volume = Column(Float)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    observation_unit = relationship("ObservationUnit", back_populates="samples")
    germplasm = relationship("Germplasm")
    study = relationship("Study")


class Image(BaseModel):
    """BrAPI Image - An image associated with an observation unit"""
    
    __tablename__ = "images"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_unit_id = Column(Integer, ForeignKey("observation_units.id"), index=True)
    observation_db_id = Column(String(255))
    image_db_id = Column(String(255), unique=True, index=True)
    image_name = Column(String(255), nullable=False, index=True)
    image_file_name = Column(String(255))
    image_file_size = Column(Integer)
    image_height = Column(Integer)
    image_width = Column(Integer)
    mime_type = Column(String(100))
    image_url = Column(Text)
    image_time_stamp = Column(String(50))
    copyright = Column(String(255))
    description = Column(Text)
    descriptive_ontology_terms = Column(JSON)
    image_location = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    observation_unit = relationship("ObservationUnit", back_populates="images")


class Event(BaseModel):
    """BrAPI Event - An event that occurred during a study"""
    
    __tablename__ = "events"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    event_db_id = Column(String(255), unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_type_db_id = Column(String(255))
    event_description = Column(Text)
    date = Column(String(50))
    observation_unit_db_ids = Column(JSON)
    event_parameters = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    study = relationship("Study")
