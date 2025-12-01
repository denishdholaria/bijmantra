"""
BrAPI Core Module Models
Programs, Trials, Studies, Locations, People, Lists
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import BaseModel


class Organization(BaseModel):
    """Organization model for multi-tenancy"""
    
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    contact_email = Column(String(255))
    website = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    programs = relationship("Program", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")


class User(BaseModel):
    """User model for authentication"""
    
    __tablename__ = "users"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")


class Program(BaseModel):
    """BrAPI Program - A breeding program"""
    
    __tablename__ = "programs"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_db_id = Column(String(255), unique=True, index=True)
    program_name = Column(String(255), nullable=False, index=True)
    abbreviation = Column(String(50))
    objective = Column(Text)
    lead_person_db_id = Column(Integer, ForeignKey("people.id"))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization", back_populates="programs")
    lead_person = relationship("Person", foreign_keys=[lead_person_db_id])
    trials = relationship("Trial", back_populates="program", cascade="all, delete-orphan")


class Location(BaseModel):
    """BrAPI Location - Physical location with spatial data"""
    
    __tablename__ = "locations"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    location_db_id = Column(String(255), unique=True, index=True)
    location_name = Column(String(255), nullable=False, index=True)
    location_type = Column(String(50))
    abbreviation = Column(String(50))
    
    # Address information
    country_name = Column(String(100))
    country_code = Column(String(3))
    institute_name = Column(String(255))
    institute_address = Column(Text)
    
    # Spatial data (PostGIS)
    coordinates = Column(Geometry('POINT', srid=4326))
    coordinate_uncertainty = Column(String(50))
    coordinate_description = Column(Text)
    
    # Altitude
    altitude = Column(String(50))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    trials = relationship("Trial", back_populates="location")
    studies = relationship("Study", back_populates="location")


class Trial(BaseModel):
    """BrAPI Trial - A collection of studies"""
    
    __tablename__ = "trials"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    
    trial_db_id = Column(String(255), unique=True, index=True)
    trial_name = Column(String(255), nullable=False, index=True)
    trial_description = Column(Text)
    trial_type = Column(String(100))
    
    # Dates
    start_date = Column(String(50))
    end_date = Column(String(50))
    
    # BrAPI fields
    active = Column(Boolean, default=True)
    common_crop_name = Column(String(100))
    document_ids = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    program = relationship("Program", back_populates="trials")
    location = relationship("Location", back_populates="trials")
    studies = relationship("Study", back_populates="trial", cascade="all, delete-orphan")


class Study(BaseModel):
    """BrAPI Study - A specific study within a trial"""
    
    __tablename__ = "studies"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    
    study_db_id = Column(String(255), unique=True, index=True)
    study_name = Column(String(255), nullable=False, index=True)
    study_description = Column(Text)
    study_type = Column(String(100))
    study_code = Column(String(100))
    
    # Dates
    start_date = Column(String(50))
    end_date = Column(String(50))
    
    # BrAPI fields
    active = Column(Boolean, default=True)
    common_crop_name = Column(String(100))
    cultural_practices = Column(Text)
    observation_levels = Column(JSON)
    observation_units_description = Column(Text)
    
    # License and publication
    license = Column(String(255))
    data_links = Column(JSON)
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    trial = relationship("Trial", back_populates="studies")
    location = relationship("Location", back_populates="studies")


class Person(BaseModel):
    """BrAPI Person - Contact information"""
    
    __tablename__ = "people"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    person_db_id = Column(String(255), unique=True, index=True)
    
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    
    email_address = Column(String(255))
    phone_number = Column(String(50))
    mailing_address = Column(Text)
    
    user_id = Column(String(255))
    
    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
