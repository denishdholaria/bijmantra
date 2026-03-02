"""
Seed Bank Division - Pydantic Schemas
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from pydantic import BaseModel, ConfigDict


class VaultType(StrEnum):
    BASE = "base"
    ACTIVE = "active"
    CRYO = "cryo"


class VaultStatus(StrEnum):
    OPTIMAL = "optimal"
    WARNING = "warning"
    CRITICAL = "critical"


class AccessionStatus(StrEnum):
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
    name: str | None = None
    temperature: float | None = None
    humidity: float | None = None
    status: VaultStatus | None = None


class VaultResponse(VaultBase):
    id: str
    status: VaultStatus
    last_inspection: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Accession Schemas
class AccessionBase(BaseModel):
    accession_number: str
    genus: str
    species: str
    subspecies: str | None = None
    common_name: str | None = None
    origin: str
    collection_date: datetime | None = None
    collection_site: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    vault_id: str | None = None
    acquisition_type: str | None = None
    donor_institution: str | None = None
    mls: bool = False
    pedigree: str | None = None
    notes: str | None = None


class AccessionCreate(AccessionBase):
    seed_count: int = 0


class AccessionUpdate(BaseModel):
    common_name: str | None = None
    vault_id: str | None = None
    seed_count: int | None = None
    viability: float | None = None
    status: AccessionStatus | None = None
    notes: str | None = None


class AccessionResponse(AccessionBase):
    id: str
    seed_count: int
    viability: float
    status: AccessionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessionListResponse(BaseModel):
    data: list[AccessionResponse]
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
    germinated: int | None = None
    status: str | None = None
    notes: str | None = None


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
    planned_season: str | None = None


class RegenerationTaskResponse(BaseModel):
    id: str
    accession_id: str
    reason: str
    priority: str
    target_quantity: int
    planned_season: str | None
    status: str
    harvested_quantity: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Exchange Schemas
class ExchangeCreate(BaseModel):
    type: str
    institution_name: str
    accession_ids: list[str]
    smta: bool = True
    notes: str | None = None


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
