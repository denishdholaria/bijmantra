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

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime
import uuid

from app.services.compute_engine import compute_engine, ComputeBackend
from app.services.job_service import job_service, JobStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/compute", tags=["Compute Engine"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Request/Response Models
# ============================================================================

class GBLUPRequest(BaseModel):
    """Request for GBLUP computation"""
    genotypes: List[List[float]] = Field(..., description="Genotype matrix (n x m)")
    phenotypes: List[float] = Field(..., description="Phenotype vector (n)")
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
    breeding_values: List[float]
    mean: float
    converged: bool
    compute_time_ms: float
    backend: str


class GRMRequest(BaseModel):
    """Request for GRM computation"""
    genotypes: List[List[float]] = Field(..., description="Genotype matrix (n x m)")
    method: str = Field("vanraden1", description="Method: vanraden1, vanraden2, yang")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": [[0, 1, 2, 1], [1, 1, 0, 2], [2, 0, 1, 1]],
            "method": "vanraden1"
        }
    })


class GRMResponse(BaseModel):
    """Response from GRM computation"""
    matrix: List[List[float]]
    method: str
    n_individuals: int
    n_markers: int
    compute_time_ms: float
    backend: str


class REMLRequest(BaseModel):
    """Request for REML variance estimation"""
    phenotypes: List[float]
    fixed_effects: List[List[float]]
    random_effects: List[List[float]]
    relationship_matrix: List[List[float]]
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
    backend: str
    fortran_available: bool
    numpy_version: str
    capabilities: List[str]
    active_jobs: int
    redis_available: bool
    storage_backend: str


class JobResponse(BaseModel):
    """Job status response"""
    job_id: str
    job_type: str
    status: str
    progress: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=ComputeStatusResponse)
async def get_compute_status():
    """Get compute engine status and capabilities"""
    stats = await job_service.get_stats()
    
    return ComputeStatusResponse(
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
        active_jobs=stats["running"] + stats["pending"],
        redis_available=stats["redis_available"],
        storage_backend=stats["storage_backend"]
    )


@router.post("/gblup", response_model=GBLUPResponse)
async def compute_gblup(request: GBLUPRequest):
    """
    Compute Genomic BLUP (GBLUP)
    
    Estimates genomic breeding values using marker genotypes and phenotypes.
    Uses Fortran HPC backend when available, falls back to NumPy.
    """
    import time
    start = time.time()
    
    try:
        genotypes = np.array(request.genotypes)
        phenotypes = np.array(request.phenotypes)
        
        if genotypes.shape[0] != len(phenotypes):
            raise HTTPException(
                status_code=400,
                detail=f"Dimension mismatch: {genotypes.shape[0]} genotypes vs {len(phenotypes)} phenotypes"
            )
        
        result = compute_engine.compute_gblup(
            genotypes=genotypes,
            phenotypes=phenotypes,
            heritability=request.heritability
        )
        
        compute_time = (time.time() - start) * 1000
        
        return GBLUPResponse(
            breeding_values=result.breeding_values.tolist(),
            mean=float(result.fixed_effects[0]) if len(result.fixed_effects) > 0 else float(phenotypes.mean()),
            converged=result.converged,
            compute_time_ms=round(compute_time, 2),
            backend=compute_engine.backend.value
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grm", response_model=GRMResponse)
async def compute_grm(request: GRMRequest):
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
        genotypes = np.array(request.genotypes)
        
        if request.method not in ["vanraden1", "vanraden2", "yang"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown method: {request.method}. Use vanraden1, vanraden2, or yang"
            )
        
        result = compute_engine.compute_grm(
            genotypes=genotypes,
            method=request.method
        )
        
        compute_time = (time.time() - start) * 1000
        
        return GRMResponse(
            matrix=result.matrix.tolist(),
            method=result.method,
            n_individuals=result.n_individuals,
            n_markers=result.n_markers,
            compute_time_ms=round(compute_time, 2),
            backend=compute_engine.backend.value
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reml", response_model=REMLResponse)
async def estimate_variance_components(request: REMLRequest):
    """
    Estimate variance components using REML
    
    Methods:
    - ai-reml: Average Information REML (faster convergence)
    - em-reml: Expectation Maximization REML (more stable)
    """
    import time
    start = time.time()
    
    try:
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
        
        return REMLResponse(
            var_additive=result.var_additive,
            var_residual=result.var_residual,
            heritability=result.heritability,
            converged=result.converged,
            iterations=result.iterations,
            compute_time_ms=round(compute_time, 2),
            backend=compute_engine.backend.value
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Background Job Support (Redis-backed)
# ============================================================================

@router.post("/gblup/async")
async def compute_gblup_async(request: GBLUPRequest, background_tasks: BackgroundTasks):
    """
    Submit GBLUP computation as background job
    
    For large datasets, use this endpoint to avoid timeout.
    Poll /compute/jobs/{job_id} for status.
    
    Job data is stored in Redis (with in-memory fallback) and auto-expires after 1 hour.
    """
    # Create job
    job_id = await job_service.create_job(
        job_type="gblup",
        metadata={
            "n_individuals": len(request.phenotypes),
            "n_markers": len(request.genotypes[0]) if request.genotypes else 0,
            "heritability": request.heritability
        }
    )
    
    # Schedule background task
    background_tasks.add_task(_run_gblup_job, job_id, request)
    
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get status of a compute job
    
    Jobs auto-expire after 1 hour.
    """
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    
    return JobResponse(**job)


@router.get("/jobs")
async def list_jobs(job_type: Optional[str] = None):
    """
    List all active compute jobs
    
    Args:
        job_type: Filter by job type (gblup, grm, reml)
    """
    jobs = await job_service.list_jobs(job_type=job_type)
    stats = await job_service.get_stats()
    
    return {
        "jobs": jobs,
        "total": len(jobs),
        "stats": stats
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a compute job"""
    success = await job_service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job deleted", "job_id": job_id}


async def _run_gblup_job(job_id: str, request: GBLUPRequest):
    """Background task for GBLUP computation"""
    import time
    
    # Update status to running
    await job_service.update_job(job_id, status=JobStatus.RUNNING, progress=0.1)
    
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
        await job_service.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            result={
                "breeding_values": result.breeding_values.tolist(),
                "mean": float(result.fixed_effects[0]) if len(result.fixed_effects) > 0 else float(phenotypes.mean()),
                "converged": result.converged,
                "compute_time_ms": round(compute_time, 2),
                "backend": compute_engine.backend.value
            }
        )
        
    except Exception as e:
        await job_service.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e)
        )
