from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.reevu_envelope import CalculationStep, EvidenceRef


COMPUTE_CONTRACT_VERSION = "compute.v1"

ApprovedRoutine = Literal["gblup", "grm", "reml"]
ApprovedOutputKind = Literal["breeding_values", "relationship_matrix", "variance_components"]
ExecutionMode = Literal["sync", "async"]
ComputeJobState = Literal["pending", "running", "completed", "failed"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ComputeInputSummary(BaseModel):
    n_observations: int | None = None
    n_individuals: int | None = None
    n_markers: int | None = None
    n_fixed_effects: int | None = None
    n_random_effects: int | None = None
    relationship_matrix_shape: list[int] | None = None
    heritability: float | None = None
    method: str | None = None
    max_iter: int | None = None
    input_snapshot_at: str | None = None
    input_reliability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    calculation_method_identifiers: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ComputeProvenance(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    routine: ApprovedRoutine
    output_kind: ApprovedOutputKind
    backend: str
    executed_at: str = Field(default_factory=_utc_now_iso)
    execution_mode: ExecutionMode
    lineage_record_id: str | None = None
    input_summary: ComputeInputSummary
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    calculation_steps: list[CalculationStep] = Field(default_factory=list)
    policy_flags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class GBLUPOutput(BaseModel):
    breeding_values: list[float]
    reliability: list[float] | None = None
    accuracy: list[float] | None = None
    genetic_variance: float | None = None
    error_variance: float | None = None
    mean: float
    converged: bool

    model_config = ConfigDict(extra="forbid")


class GRMOutput(BaseModel):
    matrix: list[list[float]]
    method: str
    n_individuals: int
    n_markers: int

    model_config = ConfigDict(extra="forbid")


class REMLOutput(BaseModel):
    var_additive: float
    var_residual: float
    heritability: float
    converged: bool
    iterations: int

    model_config = ConfigDict(extra="forbid")


class ComputeSuccessResponse(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    routine: ApprovedRoutine
    output_kind: ApprovedOutputKind
    status: Literal["succeeded"] = "succeeded"
    output: GBLUPOutput | GRMOutput | REMLOutput
    compute_time_ms: float
    provenance: ComputeProvenance

    model_config = ConfigDict(extra="forbid")


class ComputeErrorDetail(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    code: str
    message: str
    routine: ApprovedRoutine | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ComputeJobAcceptedResponse(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    routine: ApprovedRoutine
    job_id: str
    status: Literal["pending"] = "pending"
    poll_url: str
    lineage_record_id: str | None = None
    accepted_input: ComputeInputSummary

    model_config = ConfigDict(extra="forbid")


class ComputeJobResponse(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    job_id: str
    routine: ApprovedRoutine
    status: ComputeJobState
    lineage_record_id: str | None = None
    progress: float
    result: ComputeSuccessResponse | None = None
    error: ComputeErrorDetail | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None

    model_config = ConfigDict(extra="forbid")


class ComputeJobListResponse(BaseModel):
    contract_version: str = Field(default=COMPUTE_CONTRACT_VERSION)
    jobs: list[ComputeJobResponse]
    total: int
    stats: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class ApprovedRoutineDescriptor(BaseModel):
    routine: ApprovedRoutine
    output_kind: ApprovedOutputKind
    description: str
    async_supported: bool

    model_config = ConfigDict(extra="forbid")
