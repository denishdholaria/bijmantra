"""
BrAPI Core Module Schemas
Programs, Trials, Studies, Locations, People
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


# ============= Organization Schemas =============

class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    """Organization response schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= User Schemas =============

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating user"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters with at least one uppercase, one lowercase, one digit, and one special character"
    )
    organization_id: int
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """User response schema"""
    id: int
    organization_id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Program Schemas =============

class ProgramBase(BaseModel):
    """Base program schema"""
    program_name: str = Field(..., alias="programName")
    abbreviation: Optional[str] = None
    objective: Optional[str] = None
    lead_person_db_id: Optional[str] = Field(None, alias="leadPersonDbId")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class ProgramCreate(ProgramBase):
    """Schema for creating program"""
    pass


class ProgramUpdate(BaseModel):
    """Schema for updating program"""
    program_name: Optional[str] = Field(None, alias="programName")
    abbreviation: Optional[str] = None
    objective: Optional[str] = None
    lead_person_db_id: Optional[str] = Field(None, alias="leadPersonDbId")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class Program(ProgramBase):
    """Program response schema (BrAPI compliant)"""
    program_db_id: str = Field(..., alias="programDbId")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Location Schemas =============

class Coordinates(BaseModel):
    """Geographic coordinates"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None


class LocationBase(BaseModel):
    """Base location schema"""
    location_name: str = Field(..., alias="locationName")
    location_type: Optional[str] = Field(None, alias="locationType")
    abbreviation: Optional[str] = None
    country_name: Optional[str] = Field(None, alias="countryName")
    country_code: Optional[str] = Field(None, alias="countryCode")
    institute_name: Optional[str] = Field(None, alias="instituteName")
    institute_address: Optional[str] = Field(None, alias="instituteAddress")
    coordinates: Optional[Coordinates] = None
    coordinate_uncertainty: Optional[str] = Field(None, alias="coordinateUncertainty")
    coordinate_description: Optional[str] = Field(None, alias="coordinateDescription")
    altitude: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class LocationCreate(LocationBase):
    """Schema for creating location"""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating location"""
    location_name: Optional[str] = Field(None, alias="locationName")
    location_type: Optional[str] = Field(None, alias="locationType")
    abbreviation: Optional[str] = None
    country_name: Optional[str] = Field(None, alias="countryName")
    country_code: Optional[str] = Field(None, alias="countryCode")
    institute_name: Optional[str] = Field(None, alias="instituteName")
    institute_address: Optional[str] = Field(None, alias="instituteAddress")
    coordinates: Optional[Coordinates] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(populate_by_name=True)


class Location(LocationBase):
    """Location response schema (BrAPI compliant)"""
    location_db_id: str = Field(..., alias="locationDbId")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Trial Schemas =============

class TrialBase(BaseModel):
    """Base trial schema"""
    trial_name: str = Field(..., alias="trialName")
    trial_description: Optional[str] = Field(None, alias="trialDescription")
    trial_type: Optional[str] = Field(None, alias="trialType")
    program_db_id: Optional[str] = Field(None, alias="programDbId")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    active: Optional[bool] = True
    common_crop_name: Optional[str] = Field(None, alias="commonCropName")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class TrialCreate(TrialBase):
    """Schema for creating trial"""
    pass


class TrialUpdate(BaseModel):
    """Schema for updating trial"""
    trial_name: Optional[str] = Field(None, alias="trialName")
    trial_description: Optional[str] = Field(None, alias="trialDescription")
    trial_type: Optional[str] = Field(None, alias="trialType")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    active: Optional[bool] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(populate_by_name=True)


class Trial(TrialBase):
    """Trial response schema (BrAPI compliant)"""
    trial_db_id: str = Field(..., alias="trialDbId")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Study Schemas =============

class StudyBase(BaseModel):
    """Base study schema"""
    study_name: str = Field(..., alias="studyName")
    study_description: Optional[str] = Field(None, alias="studyDescription")
    study_type: Optional[str] = Field(None, alias="studyType")
    study_code: Optional[str] = Field(None, alias="studyCode")
    trial_db_id: Optional[str] = Field(None, alias="trialDbId")
    location_db_id: Optional[str] = Field(None, alias="locationDbId")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    active: Optional[bool] = True
    common_crop_name: Optional[str] = Field(None, alias="commonCropName")
    cultural_practices: Optional[str] = Field(None, alias="culturalPractices")
    observation_levels: Optional[List[Dict[str, str]]] = Field(None, alias="observationLevels")
    observation_units_description: Optional[str] = Field(None, alias="observationUnitsDescription")
    license: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class StudyCreate(StudyBase):
    """Schema for creating study"""
    pass


class StudyUpdate(BaseModel):
    """Schema for updating study"""
    study_name: Optional[str] = Field(None, alias="studyName")
    study_description: Optional[str] = Field(None, alias="studyDescription")
    study_type: Optional[str] = Field(None, alias="studyType")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    active: Optional[bool] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(populate_by_name=True)


class Study(StudyBase):
    """Study response schema (BrAPI compliant)"""
    study_db_id: str = Field(..., alias="studyDbId")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Person Schemas =============

class PersonBase(BaseModel):
    """Base person schema"""
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    middle_name: Optional[str] = Field(None, alias="middleName")
    email_address: Optional[EmailStr] = Field(None, alias="emailAddress")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    mailing_address: Optional[str] = Field(None, alias="mailingAddress")
    user_id: Optional[str] = Field(None, alias="userId")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    external_references: Optional[List[Dict[str, str]]] = Field(None, alias="externalReferences")
    
    model_config = ConfigDict(populate_by_name=True)


class PersonCreate(PersonBase):
    """Schema for creating person"""
    pass


class PersonUpdate(PersonBase):
    """Schema for updating person"""
    pass


class Person(PersonBase):
    """Person response schema (BrAPI compliant)"""
    person_db_id: str = Field(..., alias="personDbId")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
