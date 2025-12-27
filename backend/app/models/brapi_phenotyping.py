"""
BrAPI Phenotyping Reference Models
Scales, Methods, Observation Levels - Reference data for observation variables
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Scale(BaseModel):
    """BrAPI Scale - Measurement scale for observation variables"""
    
    __tablename__ = "scales"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # BrAPI identifiers
    scale_db_id = Column(String(255), unique=True, index=True)
    scale_name = Column(String(255), nullable=False, index=True)
    scale_pui = Column(String(255))
    
    # Scale definition
    data_type = Column(String(50))  # Numerical, Ordinal, Nominal, Date, Text, Code, Duration
    decimal_places = Column(Integer)
    
    # Valid values
    valid_values_min = Column(Integer)
    valid_values_max = Column(Integer)
    valid_values_categories = Column(JSON)  # List of {label, value} for categorical scales
    
    # Ontology reference
    ontology_db_id = Column(String(255))
    ontology_name = Column(String(255))
    ontology_version = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")


class Method(BaseModel):
    """BrAPI Method - Measurement method for observation variables"""
    
    __tablename__ = "methods"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # BrAPI identifiers
    method_db_id = Column(String(255), unique=True, index=True)
    method_name = Column(String(255), nullable=False, index=True)
    method_pui = Column(String(255))
    
    # Method definition
    method_class = Column(String(100))  # Measurement, Counting, Estimation, Computation
    description = Column(Text)
    formula = Column(Text)
    reference = Column(Text)
    bibliographical_reference = Column(Text)
    
    # Ontology reference
    ontology_db_id = Column(String(255))
    ontology_name = Column(String(255))
    ontology_version = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")


class ObservationLevel(BaseModel):
    """BrAPI Observation Level - Hierarchical level for observation units"""
    
    __tablename__ = "observation_levels"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Level definition
    level_name = Column(String(100), nullable=False, index=True)  # study, field, block, rep, plot, sub-plot, plant
    level_code = Column(String(50))
    level_order = Column(Integer, nullable=False)  # Hierarchy order (0 = highest)
    
    # Relationships
    organization = relationship("Organization")


class Trait(BaseModel):
    """BrAPI Trait - A characteristic being measured"""
    
    __tablename__ = "traits"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # BrAPI identifiers
    trait_db_id = Column(String(255), unique=True, index=True)
    trait_name = Column(String(255), nullable=False, index=True)
    trait_pui = Column(String(255))
    
    # Trait definition
    trait_description = Column(Text)
    trait_class = Column(String(100))  # Morphological, Phenological, Agronomic, etc.
    
    # Synonyms and alternatives
    synonyms = Column(JSON)  # List of synonym strings
    alternative_abbreviations = Column(JSON)
    main_abbreviation = Column(String(50))
    
    # Ontology reference
    ontology_db_id = Column(String(255))
    ontology_name = Column(String(255))
    
    # Entity and attribute
    entity = Column(String(255))
    attribute = Column(String(255))
    
    # Status
    status = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")


class GermplasmAttributeDefinition(BaseModel):
    """BrAPI Germplasm Attribute Definition - Definition of an attribute type"""
    
    __tablename__ = "germplasm_attribute_definitions"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # BrAPI identifiers
    attribute_db_id = Column(String(255), unique=True, index=True)
    attribute_name = Column(String(255), nullable=False, index=True)
    attribute_pui = Column(String(255))
    
    # Attribute definition
    attribute_description = Column(Text)
    attribute_category = Column(String(100))  # Morphological, Phenological, Agronomic, etc.
    
    # Common crop
    common_crop_name = Column(String(100))
    
    # Context
    context_of_use = Column(JSON)  # List of contexts
    default_value = Column(String(255))
    documentation_url = Column(Text)
    growth_stage = Column(String(100))
    institution = Column(String(255))
    language = Column(String(10))
    scientist = Column(String(255))
    status = Column(String(50))
    submission_timestamp = Column(String(50))
    synonyms = Column(JSON)
    
    # Trait info (embedded)
    trait_db_id = Column(String(255))
    trait_name = Column(String(255))
    trait_description = Column(Text)
    trait_class = Column(String(100))
    
    # Method info (embedded)
    method_db_id = Column(String(255))
    method_name = Column(String(255))
    method_description = Column(Text)
    method_class = Column(String(100))
    
    # Scale info (embedded)
    scale_db_id = Column(String(255))
    scale_name = Column(String(255))
    data_type = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")


class GermplasmAttributeValue(BaseModel):
    """BrAPI Germplasm Attribute Value - A value for a germplasm attribute"""
    
    __tablename__ = "germplasm_attribute_values"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    attribute_definition_id = Column(Integer, ForeignKey("germplasm_attribute_definitions.id"), index=True)
    
    # BrAPI identifiers
    attribute_value_db_id = Column(String(255), unique=True, index=True)
    
    # Attribute reference (denormalized for BrAPI compatibility)
    attribute_db_id = Column(String(255), index=True)
    attribute_name = Column(String(255))
    
    # Germplasm reference (denormalized for BrAPI compatibility)
    germplasm_db_id = Column(String(255), index=True)
    germplasm_name = Column(String(255))
    
    # Value
    value = Column(Text, nullable=False)
    determined_date = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm")
    attribute_definition = relationship("GermplasmAttributeDefinition")
