from __future__ import annotations

from pydantic import BaseModel, Field


GERMPLASM_LOOKUP_CONTRACT_VERSION = "germplasm_lookup.response.v1"
GERMPLASM_LOOKUP_TRUST_SURFACE = "germplasm_lookup"


class GermplasmLookupContractMetadata(BaseModel):
    response_contract_version: str = Field(default=GERMPLASM_LOOKUP_CONTRACT_VERSION)
    trust_surface: str = Field(default=GERMPLASM_LOOKUP_TRUST_SURFACE)
    data_source: str = Field(default="database")
    schema_version: str = Field(default="1")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    data_age_seconds: int | None = Field(default=None, ge=0)
