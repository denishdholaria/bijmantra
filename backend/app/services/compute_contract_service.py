from __future__ import annotations

from datetime import UTC, datetime
import json
import math
from typing import Any

from fastapi import HTTPException

from app.modules.ai.services.reevu_provenance_validator import validate_all
from app.schemas.compute_contract import (
    ApprovedOutputKind,
    ApprovedRoutine,
    ComputeErrorDetail,
    ComputeInputSummary,
    ComputeJobResponse,
    ComputeProvenance,
    ComputeSuccessResponse,
    GBLUPOutput,
    GRMOutput,
    REMLOutput,
)
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope


APPROVED_ROUTINES: tuple[dict[str, Any], ...] = (
    {
        "routine": "gblup",
        "output_kind": "breeding_values",
        "description": "Genomic breeding value estimates with convergence status and population mean.",
        "async_supported": True,
    },
    {
        "routine": "grm",
        "output_kind": "relationship_matrix",
        "description": "Genomic relationship matrix with explicit method and matrix dimensions.",
        "async_supported": False,
    },
    {
        "routine": "reml",
        "output_kind": "variance_components",
        "description": "Variance component estimates with heritability, convergence state, and iteration count.",
        "async_supported": False,
    },
)


def derive_compute_policy_flags(
    *,
    routine: ApprovedRoutine,
    output: GBLUPOutput | GRMOutput | REMLOutput | dict[str, Any],
    input_summary: ComputeInputSummary,
) -> list[str]:
    flags: set[str] = set()

    def get_output_value(field_name: str) -> Any:
        if isinstance(output, dict):
            return output.get(field_name)
        return getattr(output, field_name, None)

    heritability = input_summary.heritability
    if routine == "gblup" and heritability is not None and heritability < 0.2:
        flags.add("low_heritability")

    if routine in {"gblup", "reml"} and get_output_value("converged") is False:
        flags.add("non_convergence_warning")

    output_heritability = get_output_value("heritability")
    if routine == "reml" and isinstance(output_heritability, (int, float)) and output_heritability < 0.2:
        flags.add("low_heritability")

    return sorted(flags)


def derive_compute_input_provenance(
    *,
    routine: ApprovedRoutine,
    input_summary: ComputeInputSummary,
) -> ComputeInputSummary:
    reliability_score = 0.35

    if input_summary.n_observations is not None:
        reliability_score += 0.2 if input_summary.n_observations >= 3 else 0.1

    if input_summary.n_individuals is not None:
        reliability_score += 0.15 if input_summary.n_individuals >= 3 else 0.05

    if input_summary.heritability is not None:
        reliability_score += 0.15 if input_summary.heritability >= 0.2 else 0.05

    if routine == "grm" and input_summary.n_markers is not None and input_summary.n_individuals is not None:
        if input_summary.n_markers >= input_summary.n_individuals:
            reliability_score += 0.1

    if routine == "reml" and input_summary.max_iter is not None and input_summary.max_iter >= 25:
        reliability_score += 0.05

    method_identifiers_by_routine: dict[ApprovedRoutine, list[str]] = {
        "gblup": ["genomic_relationship_matrix", "additive_model", "blup_solver"],
        "grm": ["marker_standardization", f"grm:{input_summary.method or 'vanraden1'}"],
        "reml": [f"reml:{input_summary.method or 'ai-reml'}", "variance_component_estimation", "mixed_model_solver"],
    }

    return input_summary.model_copy(
        update={
            "input_snapshot_at": datetime.now(UTC).isoformat(),
            "input_reliability_score": round(min(reliability_score, 0.95), 2),
            "calculation_method_identifiers": method_identifiers_by_routine[routine],
        }
    )


def build_error_detail(
    *,
    code: str,
    message: str,
    routine: ApprovedRoutine | None = None,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> ComputeErrorDetail:
    return ComputeErrorDetail(
        code=code,
        message=message,
        routine=routine,
        retryable=retryable,
        details=details or {},
    )


def raise_contract_error(
    *,
    status_code: int,
    code: str,
    message: str,
    routine: ApprovedRoutine | None = None,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> None:
    error = build_error_detail(
        code=code,
        message=message,
        routine=routine,
        retryable=retryable,
        details=details,
    )
    raise HTTPException(status_code=status_code, detail=error.model_dump())


def ensure_non_empty_vector(values: list[float], *, field_name: str, routine: ApprovedRoutine) -> None:
    if not values:
        raise_contract_error(
            status_code=422,
            code="invalid_input",
            message=f"{field_name} must contain at least one value.",
            routine=routine,
            details={"field": field_name},
        )

    _ensure_finite_numbers(values, field_name=field_name, routine=routine)


def ensure_rectangular_matrix(
    matrix: list[list[float]],
    *,
    field_name: str,
    routine: ApprovedRoutine,
    allow_empty: bool = False,
) -> tuple[int, int]:
    if not matrix:
        if allow_empty:
            return (0, 0)
        raise_contract_error(
            status_code=422,
            code="invalid_input",
            message=f"{field_name} must contain at least one row.",
            routine=routine,
            details={"field": field_name},
        )

    row_length = len(matrix[0])
    if row_length == 0:
        raise_contract_error(
            status_code=422,
            code="invalid_input",
            message=f"{field_name} must contain at least one column.",
            routine=routine,
            details={"field": field_name},
        )

    for row_index, row in enumerate(matrix):
        if len(row) != row_length:
            raise_contract_error(
                status_code=422,
                code="invalid_input_shape",
                message=f"{field_name} must be rectangular.",
                routine=routine,
                details={"field": field_name, "row_index": row_index, "expected_columns": row_length, "actual_columns": len(row)},
            )
        _ensure_finite_numbers(row, field_name=f"{field_name}[{row_index}]", routine=routine)

    return (len(matrix), row_length)


def ensure_matching_length(
    *,
    actual: int,
    expected: int,
    field_name: str,
    expected_field_name: str,
    routine: ApprovedRoutine,
) -> None:
    if actual != expected:
        raise_contract_error(
            status_code=422,
            code="invalid_input_shape",
            message=f"{field_name} length must match {expected_field_name}.",
            routine=routine,
            details={
                "field": field_name,
                "expected_field": expected_field_name,
                "actual": actual,
                "expected": expected,
            },
        )


def ensure_supported_method(
    method: str,
    *,
    allowed_methods: tuple[str, ...],
    routine: ApprovedRoutine,
) -> None:
    if method not in allowed_methods:
        raise_contract_error(
            status_code=422,
            code="unsupported_method",
            message=f"Unsupported method '{method}'.",
            routine=routine,
            details={"method": method, "allowed_methods": list(allowed_methods)},
        )


def ensure_positive_number(value: float, *, field_name: str, routine: ApprovedRoutine) -> None:
    if not math.isfinite(value) or value <= 0:
        raise_contract_error(
            status_code=422,
            code="invalid_input",
            message=f"{field_name} must be a finite positive number.",
            routine=routine,
            details={"field": field_name, "value": value},
        )


def ensure_square_matrix(
    matrix: list[list[float]],
    *,
    field_name: str,
    routine: ApprovedRoutine,
) -> int:
    rows, cols = ensure_rectangular_matrix(matrix, field_name=field_name, routine=routine)
    if rows != cols:
        raise_contract_error(
            status_code=422,
            code="invalid_input_shape",
            message=f"{field_name} must be square.",
            routine=routine,
            details={"field": field_name, "rows": rows, "columns": cols},
        )
    return rows


def build_compute_success_response(
    *,
    routine: ApprovedRoutine,
    output_kind: ApprovedOutputKind,
    output: GBLUPOutput | GRMOutput | REMLOutput,
    compute_time_ms: float,
    backend: str,
    execution_mode: str,
    input_summary: ComputeInputSummary,
    method_name: str,
    lineage_record_id: str | None = None,
) -> ComputeSuccessResponse:
    input_summary = derive_compute_input_provenance(
        routine=routine,
        input_summary=input_summary,
    )
    evidence_ref = EvidenceRef(
        source_type="function",
        entity_id=f"fn:compute.{routine}",
        query_or_method=method_name,
    )
    calculation_step = CalculationStep(
        step_id=f"fn:compute.{routine}",
        formula=None,
        inputs=input_summary.model_dump(exclude_none=True),
    )
    envelope = ReevuEnvelope(
        claims=[f"{routine} computation completed successfully"],
        evidence_refs=[evidence_ref],
        calculation_steps=[calculation_step],
    )
    policy_flags = sorted({
        *validate_all(envelope),
        *derive_compute_policy_flags(
            routine=routine,
            output=output,
            input_summary=input_summary,
        ),
    })
    provenance = ComputeProvenance(
        routine=routine,
        output_kind=output_kind,
        backend=backend,
        execution_mode=execution_mode,
        lineage_record_id=lineage_record_id,
        input_summary=input_summary,
        evidence_refs=[evidence_ref],
        calculation_steps=[calculation_step],
        policy_flags=policy_flags,
    )
    return ComputeSuccessResponse(
        routine=routine,
        output_kind=output_kind,
        output=output,
        compute_time_ms=round(compute_time_ms, 2),
        provenance=provenance,
    )


def serialize_error_detail(error: ComputeErrorDetail) -> str:
    return error.model_dump_json()


def parse_error_detail(raw_error: Any, *, routine: ApprovedRoutine | None = None) -> ComputeErrorDetail | None:
    if raw_error is None:
        return None

    if isinstance(raw_error, dict):
        return ComputeErrorDetail.model_validate(raw_error)

    if isinstance(raw_error, str):
        try:
            return ComputeErrorDetail.model_validate(json.loads(raw_error))
        except (json.JSONDecodeError, ValueError):
            return build_error_detail(
                code="computation_failed",
                message="The compute job failed.",
                routine=routine,
                retryable=False,
                details={"raw_error": raw_error},
            )

    return build_error_detail(
        code="computation_failed",
        message="The compute job failed.",
        routine=routine,
        retryable=False,
    )


def build_job_response(job: dict[str, Any]) -> ComputeJobResponse:
    routine = _normalize_job_routine(job.get("job_type"))
    result = _normalize_job_result(job.get("result"), routine=routine)
    return ComputeJobResponse(
        job_id=job["job_id"],
        routine=routine,
        status=job["status"],
        lineage_record_id=(job.get("metadata") or {}).get("lineage_record_id"),
        progress=job["progress"],
        result=ComputeSuccessResponse.model_validate(result) if result else None,
        error=parse_error_detail(job.get("error"), routine=routine),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        completed_at=job.get("completed_at"),
    )


def _normalize_job_routine(job_type: str | None) -> ApprovedRoutine:
    if job_type in {"gblup", "grm", "reml"}:
        return job_type
    return "gblup"


def _normalize_job_result(result: Any, *, routine: ApprovedRoutine) -> dict[str, Any] | None:
    if result is None:
        return None

    if isinstance(result, dict) and {"contract_version", "routine", "output_kind", "status", "output", "compute_time_ms", "provenance"}.issubset(result.keys()):
        return result

    if isinstance(result, dict) and routine == "gblup" and {"breeding_values", "mean", "converged", "compute_time_ms", "backend"}.issubset(result.keys()):
        breeding_values = result.get("breeding_values") or []
        return build_compute_success_response(
            routine="gblup",
            output_kind="breeding_values",
            output={
                "breeding_values": breeding_values,
                "mean": result["mean"],
                "converged": result["converged"],
            },
            compute_time_ms=result["compute_time_ms"],
            backend=result["backend"],
            execution_mode="async",
            input_summary=ComputeInputSummary(
                n_observations=len(breeding_values),
                n_individuals=len(breeding_values),
            ),
            method_name="compute_engine.compute_gblup",
        ).model_dump()

    return None


def _ensure_finite_numbers(values: list[float], *, field_name: str, routine: ApprovedRoutine) -> None:
    for index, value in enumerate(values):
        if not math.isfinite(value):
            raise_contract_error(
                status_code=422,
                code="invalid_numeric_value",
                message=f"{field_name} must contain only finite numeric values.",
                routine=routine,
                details={"field": field_name, "index": index, "value": value},
            )
