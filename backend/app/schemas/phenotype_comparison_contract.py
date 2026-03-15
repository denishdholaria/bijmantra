from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


PHENOTYPE_COMPARISON_CONTRACT_VERSION = "phenotype_comparison.response.v1"
PHENOTYPE_COMPARISON_TRUST_SURFACE = "phenotype_comparison"


class PhenotypeComparisonContractMetadata(BaseModel):
    contract_version: str = Field(default=PHENOTYPE_COMPARISON_CONTRACT_VERSION)
    trust_surface: str = Field(default=PHENOTYPE_COMPARISON_TRUST_SURFACE)
    source: str = Field(default="database")
    scope: str


def attach_contract_metadata(payload: dict[str, Any], *, scope: str) -> dict[str, Any]:
    metadata = PhenotypeComparisonContractMetadata(scope=scope).model_dump()
    return {**metadata, **payload}