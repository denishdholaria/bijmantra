"""
BrAPI Core Module Schemas
Programs, Trials, Studies, Locations, People
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============= Organization Schemas =============

class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str
    description: str | None = None
    contact_email: EmailStr | None = None
    website: str | None = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: str | None = None
    description: str | None = None
    contact_email: EmailStr | None = None
    website: str | None = None
    is_active: bool | None = None


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
    full_name: str | None = None


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
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None


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
    abbreviation: str | None = None
    objective: str | None = None
    lead_person_db_id: str | None = Field(None, alias="leadPersonDbId")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class ProgramCreate(ProgramBase):
    """Schema for creating program"""
    pass


class ProgramUpdate(BaseModel):
    """Schema for updating program"""
    program_name: str | None = Field(None, alias="programName")
    abbreviation: str | None = None
    objective: str | None = None
    lead_person_db_id: str | None = Field(None, alias="leadPersonDbId")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

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
    altitude: float | None = None


class LocationBase(BaseModel):
    """Base location schema"""
    location_name: str = Field(..., alias="locationName")
    location_type: str | None = Field(None, alias="locationType")
    abbreviation: str | None = None
    country_name: str | None = Field(None, alias="countryName")
    country_code: str | None = Field(None, alias="countryCode")
    institute_name: str | None = Field(None, alias="instituteName")
    institute_address: str | None = Field(None, alias="instituteAddress")
    coordinates: Coordinates | None = None
    coordinate_uncertainty: str | None = Field(None, alias="coordinateUncertainty")
    coordinate_description: str | None = Field(None, alias="coordinateDescription")
    altitude: str | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class LocationCreate(LocationBase):
    """Schema for creating location"""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating location"""
    location_name: str | None = Field(None, alias="locationName")
    location_type: str | None = Field(None, alias="locationType")
    abbreviation: str | None = None
    country_name: str | None = Field(None, alias="countryName")
    country_code: str | None = Field(None, alias="countryCode")
    institute_name: str | None = Field(None, alias="instituteName")
    institute_address: str | None = Field(None, alias="instituteAddress")
    coordinates: Coordinates | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)


class Location(LocationBase):
    """Location response schema (BrAPI compliant)"""
    location_db_id: str = Field(..., alias="locationDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Trial Schemas =============

class TrialBase(BaseModel):
    """Base trial schema"""
    trial_name: str = Field(..., alias="trialName")
    trial_description: str | None = Field(None, alias="trialDescription")
    trial_type: str | None = Field(None, alias="trialType")
    program_db_id: str | None = Field(None, alias="programDbId")
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")
    active: bool | None = True
    common_crop_name: str | None = Field(None, alias="commonCropName")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class TrialCreate(TrialBase):
    """Schema for creating trial"""
    pass


class TrialUpdate(BaseModel):
    """Schema for updating trial"""
    trial_name: str | None = Field(None, alias="trialName")
    trial_description: str | None = Field(None, alias="trialDescription")
    trial_type: str | None = Field(None, alias="trialType")
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")
    active: bool | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)


class Trial(TrialBase):
    """Trial response schema (BrAPI compliant)"""
    trial_db_id: str = Field(..., alias="trialDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Study Schemas =============

class StudyBase(BaseModel):
    """Base study schema"""
    study_name: str = Field(..., alias="studyName")
    study_description: str | None = Field(None, alias="studyDescription")
    study_type: str | None = Field(None, alias="studyType")
    study_code: str | None = Field(None, alias="studyCode")
    trial_db_id: str | None = Field(None, alias="trialDbId")
    location_db_id: str | None = Field(None, alias="locationDbId")
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")
    active: bool | None = True
    common_crop_name: str | None = Field(None, alias="commonCropName")
    cultural_practices: str | None = Field(None, alias="culturalPractices")
    observation_levels: list[dict[str, str]] | None = Field(None, alias="observationLevels")
    observation_units_description: str | None = Field(None, alias="observationUnitsDescription")
    license: str | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class StudyCreate(StudyBase):
    """Schema for creating study"""
    pass


class StudyUpdate(BaseModel):
    """Schema for updating study"""
    study_name: str | None = Field(None, alias="studyName")
    study_description: str | None = Field(None, alias="studyDescription")
    study_type: str | None = Field(None, alias="studyType")
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")
    active: bool | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)


class Study(StudyBase):
    """Study response schema (BrAPI compliant)"""
    study_db_id: str = Field(..., alias="studyDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============= Person Schemas =============

class PersonBase(BaseModel):
    """Base person schema"""
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    middle_name: str | None = Field(None, alias="middleName")
    email_address: EmailStr | None = Field(None, alias="emailAddress")
    phone_number: str | None = Field(None, alias="phoneNumber")
    mailing_address: str | None = Field(None, alias="mailingAddress")
    user_id: str | None = Field(None, alias="userId")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

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

# ============= Season Schemas =============

class SeasonBase(BaseModel):
    """Base season schema"""
    season_name: str = Field(..., alias="seasonName")
    year: int | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class SeasonCreate(SeasonBase):
    """Schema for creating season"""
    pass


class SeasonUpdate(BaseModel):
    """Schema for updating season"""
    season_name: str | None = Field(None, alias="seasonName")
    year: int | None = None
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")
    external_references: list[dict[str, str]] | None = Field(None, alias="externalReferences")

    model_config = ConfigDict(populate_by_name=True)


class Season(SeasonBase):
    """Season response schema (BrAPI compliant)"""
    season_db_id: str = Field(..., alias="seasonDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
