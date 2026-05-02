from __future__ import annotations

from pydantic import BaseModel, Field


TRIAL_SUMMARY_CONTRACT_VERSION = "trial_summary.response.v1"
TRIAL_SUMMARY_TRUST_SURFACE = "trial_summary"


class TrialSummaryContractMetadata(BaseModel):
    response_contract_version: str = Field(default=TRIAL_SUMMARY_CONTRACT_VERSION)
    trust_surface: str = Field(default=TRIAL_SUMMARY_TRUST_SURFACE)
    data_source: str = Field(default="database")
    schema_version: str = Field(default="1")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    data_age_seconds: int | None = Field(default=None, ge=0)
    calculation_method_refs: list[str] = Field(default_factory=list)