from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


PHENOTYPE_COMPARISON_CONTRACT_VERSION = "phenotype_comparison.response.v1"
PHENOTYPE_COMPARISON_TRUST_SURFACE = "phenotype_comparison"
PHENOTYPE_COMPARISON_SCHEMA_VERSION = "1"


class PhenotypeComparisonContractMetadata(BaseModel):
    response_contract_version: str = Field(default=PHENOTYPE_COMPARISON_CONTRACT_VERSION)
    trust_surface: str = Field(default=PHENOTYPE_COMPARISON_TRUST_SURFACE)
    data_source: str = Field(default="database")
    schema_version: str = Field(default=PHENOTYPE_COMPARISON_SCHEMA_VERSION)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    data_age_seconds: int | None = Field(default=None, ge=0)
    scope: str


def attach_contract_metadata(
    payload: dict[str, Any],
    *,
    scope: str,
    confidence_score: float | None = None,
    data_age_seconds: int | None = None,
) -> dict[str, Any]:
    metadata = PhenotypeComparisonContractMetadata(
        scope=scope,
        confidence_score=confidence_score,
        data_age_seconds=data_age_seconds,
    ).model_dump()
    return {
        **metadata,
        "contract_version": metadata["response_contract_version"],
        "source": metadata["data_source"],
        **payload,
    }