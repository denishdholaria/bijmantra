from datetime import datetime

from pydantic import BaseModel


class VariantSetCreate(BaseModel):
    variant_set_name: str
    study_id: int | None = None
    reference_set_id: int | None = None
    description: str | None = None

class VCFImportResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    variant_set_id: int | None = None
    sample_count: int = 0
    variant_count: int = 0

class GenotypeMatrixInfo(BaseModel):
    variant_set_id: int
    variant_set_name: str
    sample_count: int
    variant_count: int
    storage_path: str
    created_at: datetime
