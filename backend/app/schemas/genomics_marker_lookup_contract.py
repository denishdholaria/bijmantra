from __future__ import annotations

from pydantic import BaseModel, Field


GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION = "genomics_marker_lookup.response.v1"
GENOMICS_MARKER_LOOKUP_TRUST_SURFACE = "genomics_marker_lookup"


class GenomicsMarkerLookupContractMetadata(BaseModel):
    response_contract_version: str = Field(default=GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION)
    trust_surface: str = Field(default=GENOMICS_MARKER_LOOKUP_TRUST_SURFACE)
    data_source: str = Field(default="database")
    schema_version: str = Field(default="1")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
