"""
BrAPI Germplasm Module Models
Germplasm, Attributes, Crosses, Seedlots
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Germplasm(BaseModel):
    """BrAPI Germplasm - Genetic material"""
    
    __tablename__ = "germplasm"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # BrAPI identifiers
    germplasm_db_id = Column(String(255), unique=True, index=True)
    germplasm_pui = Column(String(255), index=True)  # Permanent Unique Identifier
    germplasm_name = Column(String(255), nullable=False, index=True)
    default_display_name = Column(String(255))
    accession_number = Column(String(255), index=True)
    
    # Taxonomy
    common_crop_name = Column(String(100), index=True)
    genus = Column(String(100), index=True)
    species = Column(String(255))
    species_authority = Column(String(255))
    subtaxa = Column(String(255))
    subtaxa_authority = Column(String(255))
    
    # Origin
    country_of_origin_code = Column(String(3))
    institute_code = Column(String(50))
    institute_name = Column(String(255))
    biological_status_of_accession_code = Column(String(10))
    biological_status_of_accession_description = Column(String(255))
    
    # Breeding
    pedigree = Column(Text)
    breeding_method_db_id = Column(String(255))
    
    # Seed source
    seed_source = Column(String(255))
    seed_source_description = Column(Text)
    
    # Acquisition
    acquisition_date = Column(Date)
    acquisition_source_code = Column(String(10))
    
    # Collection
    collection_date = Column(Date)
    collection_site = Column(Text)
    
    # Storage
    storage_types = Column(JSON)  # List of storage type codes
    
    # Synonyms
    synonyms = Column(JSON)  # List of synonym strings
    
    # Donors
    donors = Column(JSON)  # List of donor objects
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Lineage
    cross_id = Column(Integer, ForeignKey("crosses.id"), index=True)
    
    # Relationships
    organization = relationship("Organization")
    attributes = relationship("GermplasmAttribute", back_populates="germplasm", cascade="all, delete-orphan")
    cross = relationship("Cross", foreign_keys=[cross_id], backref="progeny")


class GermplasmAttribute(BaseModel):
    """BrAPI Germplasm Attribute - Attribute values for germplasm"""
    
    __tablename__ = "germplasm_attributes"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    attribute_db_id = Column(String(255), index=True)
    
    # Attribute definition
    attribute_name = Column(String(255), nullable=False)
    attribute_category = Column(String(100))
    attribute_description = Column(Text)
    
    # Value
    value = Column(Text)
    
    # Determination date
    determination_date = Column(Date)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm", back_populates="attributes")


class Cross(BaseModel):
    """BrAPI Cross - A cross between two germplasm"""
    
    __tablename__ = "crosses"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crossing_project_id = Column(Integer, ForeignKey("crossing_projects.id"), index=True)
    
    cross_db_id = Column(String(255), unique=True, index=True)
    cross_name = Column(String(255), nullable=False)
    cross_type = Column(String(50))  # BIPARENTAL, SELF, OPEN_POLLINATED, etc.
    
    # Parents
    parent1_db_id = Column(Integer, ForeignKey("germplasm.id"))
    parent1_type = Column(String(20))  # FEMALE, MALE, SELF, POPULATION
    parent2_db_id = Column(Integer, ForeignKey("germplasm.id"))
    parent2_type = Column(String(20))
    
    # Crossing info
    crossing_year = Column(Integer)
    pollination_time_stamp = Column(String(50))
    
    # Status
    cross_status = Column(String(50))  # PLANNED, COMPLETED, FAILED
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    crossing_project = relationship("CrossingProject", back_populates="crosses")
    parent1 = relationship("Germplasm", foreign_keys=[parent1_db_id])
    parent2 = relationship("Germplasm", foreign_keys=[parent2_db_id])


from app.models.core import Program, Location
# Accession imported via string reference to avoid circular import


class CrossingProject(BaseModel):
    """BrAPI Crossing Project - A project containing multiple crosses"""
    
    __tablename__ = "crossing_projects"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), index=True)
    
    crossing_project_db_id = Column(String(255), unique=True, index=True)
    crossing_project_name = Column(String(255), nullable=False)
    crossing_project_description = Column(Text)
    
    # Common crop
    common_crop_name = Column(String(100))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    program = relationship(Program)
    crosses = relationship("Cross", back_populates="crossing_project", cascade="all, delete-orphan")


class PlannedCross(BaseModel):
    """BrAPI Planned Cross - A planned cross not yet executed"""
    
    __tablename__ = "planned_crosses"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crossing_project_id = Column(Integer, ForeignKey("crossing_projects.id"), index=True)
    
    planned_cross_db_id = Column(String(255), unique=True, index=True)
    planned_cross_name = Column(String(255))
    cross_type = Column(String(50))
    
    # Parents
    parent1_db_id = Column(Integer, ForeignKey("germplasm.id"))
    parent1_type = Column(String(20))
    parent2_db_id = Column(Integer, ForeignKey("germplasm.id"))
    parent2_type = Column(String(20))
    
    # Planning info
    number_of_progeny = Column(Integer)
    status = Column(String(50))  # PLANNED, IN_PROGRESS, COMPLETED
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    crossing_project = relationship("CrossingProject")
    parent1 = relationship("Germplasm", foreign_keys=[parent1_db_id])
    parent2 = relationship("Germplasm", foreign_keys=[parent2_db_id])


class Seedlot(BaseModel):
    """BrAPI Seedlot - A physical lot of seeds"""
    
    __tablename__ = "seedlots"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), index=True)
    
    seedlot_db_id = Column(String(255), unique=True, index=True)
    seedlot_name = Column(String(255), nullable=False)
    seedlot_description = Column(Text)
    
    # Conservation Link
    accession_uuid = Column(UUID(as_uuid=True), ForeignKey("seed_bank_accessions.id"), nullable=True, index=True)
    
    # Source
    source_collection = Column(String(255))
    
    # Storage
    storage_location = Column(String(255))
    
    # Quantity
    count = Column(Integer)
    units = Column(String(50))
    
    # Dates
    creation_date = Column(Date)
    last_updated = Column(Date)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm")
    accession = relationship("Accession")
    location = relationship(Location)
    program = relationship(Program)
    transactions = relationship("SeedlotTransaction", back_populates="seedlot", cascade="all, delete-orphan")


class SeedlotTransaction(BaseModel):
    """BrAPI Seedlot Transaction - Movement of seeds in/out of seedlot"""
    
    __tablename__ = "seedlot_transactions"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    seedlot_id = Column(Integer, ForeignKey("seedlots.id"), nullable=False, index=True)
    
    transaction_db_id = Column(String(255), unique=True, index=True)
    transaction_description = Column(Text)
    transaction_timestamp = Column(String(50))
    
    # Amount
    amount = Column(Float)
    units = Column(String(50))
    
    # Source/Destination
    from_seedlot_db_id = Column(String(255))
    to_seedlot_db_id = Column(String(255))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    seedlot = relationship("Seedlot", back_populates="transactions")


class BreedingMethod(BaseModel):
    """BrAPI Breeding Method - Method used to create germplasm"""
    
    __tablename__ = "breeding_methods"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    breeding_method_db_id = Column(String(255), unique=True, index=True)
    breeding_method_name = Column(String(255), nullable=False)
    abbreviation = Column(String(50))
    description = Column(Text)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
