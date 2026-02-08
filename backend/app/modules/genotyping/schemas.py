from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class VariantSetCreate(BaseModel):
    variant_set_name: str
    study_id: Optional[int] = None
    reference_set_id: Optional[int] = None
    description: Optional[str] = None
    
class VCFImportResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    variant_set_id: Optional[int] = None
    sample_count: int = 0
    variant_count: int = 0

class GenotypeMatrixInfo(BaseModel):
    variant_set_id: int
    variant_set_name: str
    sample_count: int
    variant_count: int
    storage_path: str
    created_at: datetime
