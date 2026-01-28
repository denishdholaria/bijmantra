"""
Seed Bank Division - Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class VaultType(str, Enum):
    BASE = "base"
    ACTIVE = "active"
    CRYO = "cryo"


class VaultStatus(str, Enum):
    OPTIMAL = "optimal"
    WARNING = "warning"
    CRITICAL = "critical"


class AccessionStatus(str, Enum):
    ACTIVE = "active"
    DEPLETED = "depleted"
    REGENERATING = "regenerating"


# Vault Schemas
class VaultBase(BaseModel):
    name: str
    type: VaultType
    temperature: float
    humidity: float
    capacity: int
    used: int = 0


class VaultCreate(VaultBase):
    pass


class VaultUpdate(BaseModel):
    name: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    status: Optional[VaultStatus] = None


class VaultResponse(VaultBase):
    id: str
    status: VaultStatus
    last_inspection: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Accession Schemas
class AccessionBase(BaseModel):
    accession_number: str
    genus: str
    species: str
    subspecies: Optional[str] = None
    common_name: Optional[str] = None
    origin: str
    collection_date: Optional[datetime] = None
    collection_site: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    vault_id: Optional[str] = None
    acquisition_type: Optional[str] = None
    donor_institution: Optional[str] = None
    mls: bool = False
    pedigree: Optional[str] = None
    notes: Optional[str] = None


class AccessionCreate(AccessionBase):
    seed_count: int = 0


class AccessionUpdate(BaseModel):
    common_name: Optional[str] = None
    vault_id: Optional[str] = None
    seed_count: Optional[int] = None
    viability: Optional[float] = None
    status: Optional[AccessionStatus] = None
    notes: Optional[str] = None


class AccessionResponse(AccessionBase):
    id: str
    seed_count: int
    viability: float
    status: AccessionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessionListResponse(BaseModel):
    data: List[AccessionResponse]
    total: int
    page: int
    page_size: int


# Viability Test Schemas
class ViabilityTestBase(BaseModel):
    accession_id: str
    test_date: datetime
    seeds_tested: int


class ViabilityTestCreate(ViabilityTestBase):
    pass


class ViabilityTestUpdate(BaseModel):
    germinated: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ViabilityTestResponse(ViabilityTestBase):
    id: str
    batch_number: str
    germinated: int
    germination_rate: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Regeneration Task Schemas
class RegenerationTaskCreate(BaseModel):
    accession_id: str
    reason: str
    priority: str = "medium"
    target_quantity: int
    planned_season: Optional[str] = None


class RegenerationTaskResponse(BaseModel):
    id: str
    accession_id: str
    reason: str
    priority: str
    target_quantity: int
    planned_season: Optional[str]
    status: str
    harvested_quantity: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Exchange Schemas
class ExchangeCreate(BaseModel):
    type: str
    institution_name: str
    accession_ids: List[str]
    smta: bool = True
    notes: Optional[str] = None


class ExchangeResponse(BaseModel):
    id: str
    request_number: str
    type: str
    institution_name: str
    accession_count: int
    status: str
    request_date: datetime
    smta: bool

    model_config = ConfigDict(from_attributes=True)
