from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr


class ComplianceType(StrEnum):
    ISTA = "ISTA"
    OECD = "OECD"

class SeedBatchInfo(BaseModel):
    batch_id: str
    crop: str
    variety: str
    weight_kg: float
    germination_percentage: float
    purity_percentage: float
    moisture_percentage: float
    origin_country: str

class CertificateRequest(BaseModel):
    compliance_type: ComplianceType
    seed_batch: SeedBatchInfo
    issuer_name: str
    notes: str | None = None

class CertificateResponse(BaseModel):
    id: int
    certificate_hash: str
    created_at: datetime
    status: str
    download_url: str | None = None
    verification_url: str

class BatchGenerationRequest(BaseModel):
    compliance_type: ComplianceType
    batches: list[SeedBatchInfo]
    issuer_name: str
    email_to: EmailStr

class BatchGenerationResponse(BaseModel):
    task_id: str
    message: str
