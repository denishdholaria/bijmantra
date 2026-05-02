"""
Compute API Endpoints
High-performance breeding analytics via Fortran compute engine

Endpoints:
- POST /compute/gblup - Genomic BLUP
- POST /compute/grm - Genomic Relationship Matrix
- POST /compute/reml - REML Variance Estimation
- GET /compute/status - Compute engine status
- POST /compute/gblup/async - Async GBLUP (background job)
- GET /compute/jobs/{job_id} - Get job status
- GET /compute/jobs - List all jobs

Production-ready: Uses Redis for job tracking with in-memory fallback.
"""

from typing import Any
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.database import AsyncSessionLocal
from app.models.audit import AuditLog
from app.models.compute_lineage import ComputeLineageRecord, mark_compute_lineage_completed
from app.schemas.compute_contract import (
    COMPUTE_CONTRACT_VERSION,
    ApprovedRoutineDescriptor,
    ComputeErrorDetail,
    ComputeInputSummary,
    ComputeJobAcceptedResponse,
    ComputeJobListResponse,
    ComputeJobResponse,
    ComputeSuccessResponse,
)
from app.services.compute_engine import compute_engine
from app.services.compute_contract_service import (
    APPROVED_ROUTINES,
    build_compute_success_response,
    build_error_detail,
    build_job_response,
    ensure_matching_length,
    ensure_non_empty_vector,
    ensure_positive_number,
    ensure_rectangular_matrix,
    ensure_square_matrix,
    ensure_supported_method,
    raise_contract_error,
    serialize_error_detail,
)
from app.modules.core.services.job_service import JobStatus, job_service


router = APIRouter(prefix="/compute", tags=["Compute Engine"], dependencies=[Depends(get_current_user)])


def _current_user_field(current_user: Any, field_name: str) -> Any:
    if isinstance(current_user, dict):
        return current_user.get(field_name)
    return getattr(current_user, field_name, None)


def _summarize_compute_output(output_kind: str, output: dict[str, Any]) -> dict[str, Any]:
    if output_kind == "breeding_values":
        breeding_values = output.get("breeding_values") or []
        return {
            "breeding_value_count": len(breeding_values),
            "mean": output.get("mean"),
            "converged": output.get("converged"),
        }

    if output_kind == "relationship_matrix":
        matrix = output.get("matrix") or []
        return {
            "method": output.get("method"),
            "n_individuals": output.get("n_individuals"),
            "n_markers": output.get("n_markers"),
            "matrix_shape": [len(matrix), len(matrix[0]) if matrix else 0],
        }

    return {
        "var_additive": output.get("var_additive"),
        "var_residual": output.get("var_residual"),
        "heritability": output.get("heritability"),
        "converged": output.get("converged"),
        "iterations": output.get("iterations"),
    }


async def _persist_compute_lineage(
    *,
    lineage_record_id: str,
    current_user: Any,
    routine: str,
    execution_mode: str,
    status: str,
    contract_version: str,
    output_kind: str | None = None,
    job_id: str | None = None,
    input_summary: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
    policy_flags: list[str] | None = None,
    result_summary: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    organization_id = _current_user_field(current_user, "organization_id")
    user_id = _current_user_field(current_user, "id")

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ComputeLineageRecord).where(
                    ComputeLineageRecord.lineage_record_id == lineage_record_id
                )
            )
            record = result.scalar_one_or_none()

            if record is None:
                record = ComputeLineageRecord(
                    lineage_record_id=lineage_record_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    job_id=job_id,
                    routine=routine,
                    output_kind=output_kind,
                    execution_mode=execution_mode,
                    status=status,
                    contract_version=contract_version,
                    input_summary=input_summary,
                    provenance=provenance,
                    policy_flags=policy_flags,
                    result_summary=result_summary,
                    error=error,
                )
                db.add(record)
            else:
                record.organization_id = organization_id
                record.user_id = user_id
                record.job_id = job_id or record.job_id
                record.routine = routine
                record.output_kind = output_kind or record.output_kind
                record.execution_mode = execution_mode
                record.status = status
                record.contract_version = contract_version
                if input_summary is not None:
                    record.input_summary = input_summary
                if provenance is not None:
                    record.provenance = provenance
                if policy_flags is not None:
                    record.policy_flags = policy_flags
                if result_summary is not None:
                    record.result_summary = result_summary
                if error is not None:
                    record.error = error

            mark_compute_lineage_completed(record)
            await db.commit()
    except Exception:
        return


async def _write_compute_audit(
    *,
    current_user: Any,
    action: str,
    target_type: str,
    target_id: str,
    method: str,
    changes: dict[str, Any],
) -> None:
    organization_id = _current_user_field(current_user, "organization_id")
    user_id = _current_user_field(current_user, "id")

    try:
        async with AsyncSessionLocal() as db:
            db.add(
                AuditLog(
                    organization_id=organization_id,
                    user_id=user_id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    changes=changes,
                    method=method,
                )
            )
            await db.commit()
    except Exception:
        # Audit writes must not make compute unavailable.
        return


# ============================================================================
# Request/Response Models
# ============================================================================

class GBLUPRequest(BaseModel):
    """Request for GBLUP computation"""
    genotypes: list[list[float]] = Field(..., description="Genotype matrix (n x m)")
    phenotypes: list[float] = Field(..., description="Phenotype vector (n)")
    heritability: float = Field(0.5, ge=0.01, le=0.99, description="Heritability estimate")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": [[0, 1, 2], [1, 1, 0], [2, 0, 1]],
            "phenotypes": [2.5, 3.1, 2.8],
            "heritability": 0.4
        }
    })


class GBLUPResponse(BaseModel):
    """Response from GBLUP computation"""
    breeding_values: list[float]
    mean: float
    converged: bool
    compute_time_ms: float
    backend: str


class GRMRequest(BaseModel):
    """Request for GRM computation"""
    genotypes: list[list[float]] = Field(..., description="Genotype matrix (n x m)")
    method: str = Field("vanraden1", description="Method: vanraden1, vanraden2, yang")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": [[0, 1, 2, 1], [1, 1, 0, 2], [2, 0, 1, 1]],
            "method": "vanraden1"
        }
    })


class GRMResponse(BaseModel):
    """Response from GRM computation"""
    matrix: list[list[float]]
    method: str
    n_individuals: int
    n_markers: int
    compute_time_ms: float
    backend: str


class REMLRequest(BaseModel):
    """Request for REML variance estimation"""
    phenotypes: list[float]
    fixed_effects: list[list[float]]
    random_effects: list[list[float]]
    relationship_matrix: list[list[float]]
    var_additive_init: float = 0.5
    var_residual_init: float = 1.0
    method: str = "ai-reml"
    max_iter: int = 100


class REMLResponse(BaseModel):
    """Response from REML estimation"""
    var_additive: float
    var_residual: float
    heritability: float
    converged: bool
    iterations: int
    compute_time_ms: float
    backend: str


class ComputeStatusResponse(BaseModel):
    """Compute engine status"""
    contract_version: str
    backend: str
    fortran_available: bool
    numpy_version: str
    capabilities: list[str]
    approved_routines: list[ApprovedRoutineDescriptor]
    active_jobs: int
    redis_available: bool
    storage_backend: str


class JobResponse(BaseModel):
    """Job status response"""
    contract_version: str
    job_id: str
    routine: str
    status: str
    progress: float
    result: ComputeSuccessResponse | None = None
    error: ComputeErrorDetail | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=ComputeStatusResponse)
async def get_compute_status():
    """Get compute engine status and capabilities"""
    stats = await job_service.get_stats()

    return ComputeStatusResponse(
        contract_version=COMPUTE_CONTRACT_VERSION,
        backend=compute_engine.backend.value,
        fortran_available=compute_engine._fortran_available,
        numpy_version=np.__version__,
        capabilities=[
            "BLUP",
            "GBLUP",
            "REML (AI-REML, EM-REML)",
            "GRM (VanRaden 1, VanRaden 2, Yang)",
            "PCA/SVD",
            "LD Analysis",
            "G×E Analysis",
            "Selection Index"
        ],
        approved_routines=[ApprovedRoutineDescriptor.model_validate(item) for item in APPROVED_ROUTINES],
        active_jobs=stats["running"] + stats["pending"],
        redis_available=stats["redis_available"],
        storage_backend=stats["storage_backend"]
    )


@router.post(
    "/gblup",
    response_model=ComputeSuccessResponse,
    responses={422: {"model": ComputeErrorDetail}, 500: {"model": ComputeErrorDetail}},
)
async def compute_gblup(
    request: GBLUPRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Compute Genomic BLUP (GBLUP)

    Estimates genomic breeding values using marker genotypes and phenotypes.
    Uses Fortran HPC backend when available, falls back to NumPy.
    """
    import time
    start = time.time()

    try:
        lineage_record_id = str(uuid4())
        genotype_rows, genotype_cols = ensure_rectangular_matrix(
            request.genotypes,
            field_name="genotypes",
            routine="gblup",
        )
        ensure_non_empty_vector(request.phenotypes, field_name="phenotypes", routine="gblup")
        ensure_matching_length(
            actual=genotype_rows,
            expected=len(request.phenotypes),
            field_name="genotypes",
            expected_field_name="phenotypes",
            routine="gblup",
        )

        genotypes = np.array(request.genotypes)
        phenotypes = np.array(request.phenotypes)

        result = compute_engine.compute_gblup(
            genotypes=genotypes,
            phenotypes=phenotypes,
            heritability=request.heritability
        )

        compute_time = (time.time() - start) * 1000

        response = build_compute_success_response(
            routine="gblup",
            output_kind="breeding_values",
            output={
                "breeding_values": result.breeding_values.tolist(),
                "reliability": result.reliability.tolist() if result.reliability is not None else None,
                "accuracy": result.accuracy.tolist() if result.accuracy is not None else None,
                "genetic_variance": float(result.genetic_variance) if result.genetic_variance is not None else float(np.var(result.breeding_values)),
                "error_variance": float(result.error_variance) if result.error_variance is not None else 0.0,
                "mean": float(result.fixed_effects[0]) if len(result.fixed_effects) > 0 else float(phenotypes.mean()),
                "converged": result.converged,
            },
            compute_time_ms=compute_time,
            backend=compute_engine.backend.value,
            execution_mode="sync",
            input_summary=ComputeInputSummary(
                n_observations=len(request.phenotypes),
                n_individuals=genotype_rows,
                n_markers=genotype_cols,
                heritability=request.heritability,
            ),
            method_name="compute_engine.compute_gblup",
            lineage_record_id=lineage_record_id,
        )
        await _persist_compute_lineage(
            lineage_record_id=lineage_record_id,
            current_user=current_user,
            routine="gblup",
            output_kind="breeding_values",
            execution_mode="sync",
            status=response.status,
            contract_version=response.contract_version,
            input_summary=response.provenance.input_summary.model_dump(),
            provenance=response.provenance.model_dump(),
            policy_flags=response.provenance.policy_flags,
            result_summary=_summarize_compute_output("breeding_values", response.output.model_dump()),
        )
        await _write_compute_audit(
            current_user=current_user,
            action="COMPUTE",
            target_type="compute_run",
            target_id="gblup:sync",
            method="POST",
            changes={
                "routine": "gblup",
                "execution_mode": "sync",
                "status": response.status,
                "contract_version": response.contract_version,
                "lineage_record_id": lineage_record_id,
                "input_summary": response.provenance.input_summary.model_dump(),
                "policy_flags": response.provenance.policy_flags,
                "compute_time_ms": response.compute_time_ms,
            },
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise_contract_error(
            status_code=500,
            code="computation_failed",
            message="GBLUP computation failed.",
            routine="gblup",
            details={"exception_type": type(e).__name__},
        )


@router.post(
    "/grm",
    response_model=ComputeSuccessResponse,
    responses={422: {"model": ComputeErrorDetail}, 500: {"model": ComputeErrorDetail}},
)
async def compute_grm(
    request: GRMRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Compute Genomic Relationship Matrix (GRM)

    Methods:
    - vanraden1: VanRaden Method 1 (2008) - default
    - vanraden2: VanRaden Method 2 (2008) - weighted by heterozygosity
    - yang: Yang et al. (2010)
    """
    import time
    start = time.time()

    try:
        lineage_record_id = str(uuid4())
        genotype_rows, genotype_cols = ensure_rectangular_matrix(
            request.genotypes,
            field_name="genotypes",
            routine="grm",
        )
        ensure_supported_method(
            request.method,
            allowed_methods=("vanraden1", "vanraden2", "yang"),
            routine="grm",
        )

        genotypes = np.array(request.genotypes)

        result = compute_engine.compute_grm(
            genotypes=genotypes,
            method=request.method
        )

        compute_time = (time.time() - start) * 1000

        response = build_compute_success_response(
            routine="grm",
            output_kind="relationship_matrix",
            output={
                "matrix": result.matrix.tolist(),
                "method": result.method,
                "n_individuals": result.n_individuals,
                "n_markers": result.n_markers,
            },
            compute_time_ms=compute_time,
            backend=compute_engine.backend.value,
            execution_mode="sync",
            input_summary=ComputeInputSummary(
                n_individuals=genotype_rows,
                n_markers=genotype_cols,
                method=request.method,
            ),
            method_name="compute_engine.compute_grm",
            lineage_record_id=lineage_record_id,
        )
        await _persist_compute_lineage(
            lineage_record_id=lineage_record_id,
            current_user=current_user,
            routine="grm",
            output_kind="relationship_matrix",
            execution_mode="sync",
            status=response.status,
            contract_version=response.contract_version,
            input_summary=response.provenance.input_summary.model_dump(),
            provenance=response.provenance.model_dump(),
            policy_flags=response.provenance.policy_flags,
            result_summary=_summarize_compute_output("relationship_matrix", response.output.model_dump()),
        )
        await _write_compute_audit(
            current_user=current_user,
            action="COMPUTE",
            target_type="compute_run",
            target_id=f"grm:{request.method}",
            method="POST",
            changes={
                "routine": "grm",
                "execution_mode": "sync",
                "status": response.status,
                "contract_version": response.contract_version,
                "lineage_record_id": lineage_record_id,
                "input_summary": response.provenance.input_summary.model_dump(),
                "policy_flags": response.provenance.policy_flags,
                "compute_time_ms": response.compute_time_ms,
            },
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise_contract_error(
            status_code=500,
            code="computation_failed",
            message="GRM computation failed.",
            routine="grm",
            details={"exception_type": type(e).__name__},
        )


@router.post(
    "/reml",
    response_model=ComputeSuccessResponse,
    responses={422: {"model": ComputeErrorDetail}, 500: {"model": ComputeErrorDetail}},
)
async def estimate_variance_components(
    request: REMLRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Estimate variance components using REML

    Methods:
    - ai-reml: Average Information REML (faster convergence)
    - em-reml: Expectation Maximization REML (more stable)
    """
    import time
    start = time.time()

    try:
        lineage_record_id = str(uuid4())
        ensure_non_empty_vector(request.phenotypes, field_name="phenotypes", routine="reml")
        phenotype_count = len(request.phenotypes)
        fixed_rows, fixed_cols = ensure_rectangular_matrix(
            request.fixed_effects,
            field_name="fixed_effects",
            routine="reml",
        )
        random_rows, random_cols = ensure_rectangular_matrix(
            request.random_effects,
            field_name="random_effects",
            routine="reml",
        )
        relationship_size = ensure_square_matrix(
            request.relationship_matrix,
            field_name="relationship_matrix",
            routine="reml",
        )
        ensure_supported_method(
            request.method,
            allowed_methods=("ai-reml", "em-reml"),
            routine="reml",
        )
        ensure_positive_number(request.var_additive_init, field_name="var_additive_init", routine="reml")
        ensure_positive_number(request.var_residual_init, field_name="var_residual_init", routine="reml")
        if request.max_iter < 1:
            raise_contract_error(
                status_code=422,
                code="invalid_input",
                message="max_iter must be at least 1.",
                routine="reml",
                details={"field": "max_iter", "value": request.max_iter},
            )
        ensure_matching_length(
            actual=fixed_rows,
            expected=phenotype_count,
            field_name="fixed_effects",
            expected_field_name="phenotypes",
            routine="reml",
        )
        ensure_matching_length(
            actual=random_rows,
            expected=phenotype_count,
            field_name="random_effects",
            expected_field_name="phenotypes",
            routine="reml",
        )
        if relationship_size != random_cols:
            raise_contract_error(
                status_code=422,
                code="invalid_input_shape",
                message="relationship_matrix dimensions must match random_effects columns.",
                routine="reml",
                details={
                    "field": "relationship_matrix",
                    "relationship_matrix_size": relationship_size,
                    "random_effects_columns": random_cols,
                },
            )

        phenotypes = np.array(request.phenotypes)
        fixed_effects = np.array(request.fixed_effects)
        random_effects = np.array(request.random_effects)
        relationship_matrix = np.array(request.relationship_matrix)

        result = compute_engine.estimate_variance_components(
            phenotypes=phenotypes,
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            relationship_matrix=relationship_matrix,
            var_additive_init=request.var_additive_init,
            var_residual_init=request.var_residual_init,
            method=request.method,
            max_iter=request.max_iter
        )

        compute_time = (time.time() - start) * 1000

        response = build_compute_success_response(
            routine="reml",
            output_kind="variance_components",
            output={
                "var_additive": result.var_additive,
                "var_residual": result.var_residual,
                "heritability": result.heritability,
                "converged": result.converged,
                "iterations": result.iterations,
            },
            compute_time_ms=compute_time,
            backend=compute_engine.backend.value,
            execution_mode="sync",
            input_summary=ComputeInputSummary(
                n_observations=phenotype_count,
                n_fixed_effects=fixed_cols,
                n_random_effects=random_cols,
                relationship_matrix_shape=[relationship_size, relationship_size],
                method=request.method,
                max_iter=request.max_iter,
            ),
            method_name="compute_engine.estimate_variance_components",
            lineage_record_id=lineage_record_id,
        )
        await _persist_compute_lineage(
            lineage_record_id=lineage_record_id,
            current_user=current_user,
            routine="reml",
            output_kind="variance_components",
            execution_mode="sync",
            status=response.status,
            contract_version=response.contract_version,
            input_summary=response.provenance.input_summary.model_dump(),
            provenance=response.provenance.model_dump(),
            policy_flags=response.provenance.policy_flags,
            result_summary=_summarize_compute_output("variance_components", response.output.model_dump()),
        )
        await _write_compute_audit(
            current_user=current_user,
            action="COMPUTE",
            target_type="compute_run",
            target_id=f"reml:{request.method}",
            method="POST",
            changes={
                "routine": "reml",
                "execution_mode": "sync",
                "status": response.status,
                "contract_version": response.contract_version,
                "lineage_record_id": lineage_record_id,
                "input_summary": response.provenance.input_summary.model_dump(),
                "policy_flags": response.provenance.policy_flags,
                "compute_time_ms": response.compute_time_ms,
            },
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise_contract_error(
            status_code=500,
            code="computation_failed",
            message="REML variance estimation failed.",
            routine="reml",
            details={"exception_type": type(e).__name__},
        )


# ============================================================================
# Background Job Support (Redis-backed)
# ============================================================================

@router.post(
    "/gblup/async",
    response_model=ComputeJobAcceptedResponse,
    responses={422: {"model": ComputeErrorDetail}},
)
async def compute_gblup_async(
    request: GBLUPRequest,
    background_tasks: BackgroundTasks,
    current_user: Any = Depends(get_current_user),
):
    """
    Submit GBLUP computation as background job

    For large datasets, use this endpoint to avoid timeout.
    Poll /compute/jobs/{job_id} for status.

    Job data is stored in Redis (with in-memory fallback) and auto-expires after 1 hour.
    """
    genotype_rows, genotype_cols = ensure_rectangular_matrix(
        request.genotypes,
        field_name="genotypes",
        routine="gblup",
    )
    ensure_non_empty_vector(request.phenotypes, field_name="phenotypes", routine="gblup")
    ensure_matching_length(
        actual=genotype_rows,
        expected=len(request.phenotypes),
        field_name="genotypes",
        expected_field_name="phenotypes",
        routine="gblup",
    )

    lineage_record_id = str(uuid4())

    # Create job
    job_id = await job_service.create_job(
        job_type="gblup",
        metadata={
            "contract_version": COMPUTE_CONTRACT_VERSION,
            "lineage_record_id": lineage_record_id,
            "n_individuals": genotype_rows,
            "n_markers": genotype_cols,
            "heritability": request.heritability
        }
    )
    await _persist_compute_lineage(
        lineage_record_id=lineage_record_id,
        current_user=current_user,
        routine="gblup",
        output_kind="breeding_values",
        execution_mode="async",
        status="pending",
        contract_version=COMPUTE_CONTRACT_VERSION,
        job_id=job_id,
        input_summary={
            "n_observations": len(request.phenotypes),
            "n_individuals": genotype_rows,
            "n_markers": genotype_cols,
            "heritability": request.heritability,
        },
    )
    await _write_compute_audit(
        current_user=current_user,
        action="COMPUTE",
        target_type="compute_job",
        target_id=job_id,
        method="POST",
        changes={
            "routine": "gblup",
            "execution_mode": "async",
            "status": "accepted",
            "contract_version": COMPUTE_CONTRACT_VERSION,
            "lineage_record_id": lineage_record_id,
            "input_summary": {
                "n_observations": len(request.phenotypes),
                "n_individuals": genotype_rows,
                "n_markers": genotype_cols,
                "heritability": request.heritability,
            },
        },
    )

    # Schedule background task
    background_tasks.add_task(_run_gblup_job, job_id, request, current_user)

    return ComputeJobAcceptedResponse(
        routine="gblup",
        job_id=job_id,
        poll_url=f"/api/v2/compute/jobs/{job_id}",
        lineage_record_id=lineage_record_id,
        accepted_input=ComputeInputSummary(
            n_observations=len(request.phenotypes),
            n_individuals=genotype_rows,
            n_markers=genotype_cols,
            heritability=request.heritability,
        ),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=ComputeJobResponse,
    responses={404: {"model": ComputeErrorDetail}},
)
async def get_job_status(job_id: str):
    """
    Get status of a compute job

    Jobs auto-expire after 1 hour.
    """
    job = await job_service.get_job(job_id)
    if not job:
        raise_contract_error(
            status_code=404,
            code="job_not_found",
            message="Compute job not found or expired.",
            details={"job_id": job_id},
        )

    return build_job_response(job)


@router.get("/jobs", response_model=ComputeJobListResponse)
async def list_jobs(job_type: str | None = None):
    """
    List all active compute jobs

    Args:
        job_type: Filter by job type (gblup, grm, reml)
    """
    jobs = await job_service.list_jobs(job_type=job_type)
    stats = await job_service.get_stats()

    normalized_jobs = [build_job_response(job) for job in jobs if job.get("job_type") in {"gblup", "grm", "reml"}]
    return ComputeJobListResponse(jobs=normalized_jobs, total=len(normalized_jobs), stats=stats)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a compute job"""
    success = await job_service.delete_job(job_id)
    if not success:
        raise_contract_error(
            status_code=404,
            code="job_not_found",
            message="Compute job not found.",
            details={"job_id": job_id},
        )

    return {"message": "Job deleted", "job_id": job_id}


async def _run_gblup_job(job_id: str, request: GBLUPRequest, current_user: Any):
    """Background task for GBLUP computation"""
    import time

    job = await job_service.get_job(job_id)
    lineage_record_id = ((job or {}).get("metadata") or {}).get("lineage_record_id") or str(uuid4())

    # Update status to running
    await job_service.update_job(job_id, status=JobStatus.RUNNING, progress=0.1)
    await _persist_compute_lineage(
        lineage_record_id=lineage_record_id,
        current_user=current_user,
        routine="gblup",
        output_kind="breeding_values",
        execution_mode="async",
        status="running",
        contract_version=COMPUTE_CONTRACT_VERSION,
        job_id=job_id,
    )

    try:
        start = time.time()
        genotypes = np.array(request.genotypes)
        phenotypes = np.array(request.phenotypes)

        await job_service.update_job(job_id, progress=0.3)

        result = compute_engine.compute_gblup(
            genotypes=genotypes,
            phenotypes=phenotypes,
            heritability=request.heritability
        )

        compute_time = (time.time() - start) * 1000

        # Update with result
        success_response = build_compute_success_response(
            routine="gblup",
            output_kind="breeding_values",
            output={
                "breeding_values": result.breeding_values.tolist(),
                "reliability": result.reliability.tolist() if result.reliability is not None else None,
                "accuracy": result.accuracy.tolist() if result.accuracy is not None else None,
                "genetic_variance": float(result.genetic_variance) if result.genetic_variance is not None else float(np.var(result.breeding_values)),
                "error_variance": float(result.error_variance) if result.error_variance is not None else 0.0,
                "mean": float(result.fixed_effects[0]) if len(result.fixed_effects) > 0 else float(phenotypes.mean()),
                "converged": result.converged,
            },
            compute_time_ms=compute_time,
            backend=compute_engine.backend.value,
            execution_mode="async",
            input_summary=ComputeInputSummary(
                n_observations=len(request.phenotypes),
                n_individuals=len(request.genotypes),
                n_markers=len(request.genotypes[0]) if request.genotypes else 0,
                heritability=request.heritability,
            ),
            method_name="compute_engine.compute_gblup",
            lineage_record_id=lineage_record_id,
        )
        await job_service.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            result=success_response.model_dump(),
        )
        await _persist_compute_lineage(
            lineage_record_id=lineage_record_id,
            current_user=current_user,
            routine="gblup",
            output_kind="breeding_values",
            execution_mode="async",
            status="completed",
            contract_version=success_response.contract_version,
            job_id=job_id,
            input_summary=success_response.provenance.input_summary.model_dump(),
            provenance=success_response.provenance.model_dump(),
            policy_flags=success_response.provenance.policy_flags,
            result_summary=_summarize_compute_output("breeding_values", success_response.output.model_dump()),
        )
        await _write_compute_audit(
            current_user=current_user,
            action="COMPUTE",
            target_type="compute_job",
            target_id=job_id,
            method="TASK",
            changes={
                "routine": "gblup",
                "execution_mode": "async",
                "status": "completed",
                "contract_version": success_response.contract_version,
                "lineage_record_id": lineage_record_id,
                "input_summary": success_response.provenance.input_summary.model_dump(),
                "policy_flags": success_response.provenance.policy_flags,
                "compute_time_ms": success_response.compute_time_ms,
            },
        )

    except Exception as e:
        error = build_error_detail(
            code="computation_failed",
            message="GBLUP computation failed.",
            routine="gblup",
            details={"exception_type": type(e).__name__},
        )
        await job_service.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=serialize_error_detail(error)
        )
        await _persist_compute_lineage(
            lineage_record_id=lineage_record_id,
            current_user=current_user,
            routine="gblup",
            output_kind="breeding_values",
            execution_mode="async",
            status="failed",
            contract_version=COMPUTE_CONTRACT_VERSION,
            job_id=job_id,
            error=error.model_dump(),
        )
        await _write_compute_audit(
            current_user=current_user,
            action="COMPUTE",
            target_type="compute_job",
            target_id=job_id,
            method="TASK",
            changes={
                "routine": "gblup",
                "execution_mode": "async",
                "status": "failed",
                "contract_version": COMPUTE_CONTRACT_VERSION,
                "lineage_record_id": lineage_record_id,
                "error": error.model_dump(),
            },
        )
