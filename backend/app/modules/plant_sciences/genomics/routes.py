"""
Genetics & Genomics - API Routes

Endpoints for genomic analysis and genetic tools.
Heavy computations are dispatched to Rust/Fortran engines.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from pydantic import BaseModel
import numpy as np

from app.services.compute_engine import compute_engine, ComputeBackend
from app.services.job_service import job_service, JobStatus
from app.services.genomics_data import genomics_data_service

router = APIRouter()


class GRMRequest(BaseModel):
    """Request for Genomic Relationship Matrix calculation."""
    marker_data_id: str
    method: str = "vanraden1"  # vanraden1, vanraden2, yang


class GEBVRequest(BaseModel):
    """Request for Genomic Estimated Breeding Values."""
    training_data_id: str
    target_trait: str
    model: str = "gblup"  # gblup currently supported
    heritability: float = 0.5


@router.get("/diversity")
async def genetic_diversity_summary():
    """Get genetic diversity metrics summary."""
    return {
        "metrics": {
            "expected_heterozygosity": 0.0,
            "observed_heterozygosity": 0.0,
            "fst": 0.0,
            "nei_diversity": 0.0,
        },
        "populations": [],
    }


@router.post("/grm/calculate")
async def calculate_grm(request: GRMRequest, background_tasks: BackgroundTasks):
    """
    Calculate Genomic Relationship Matrix.
    
    This is a compute-intensive operation dispatched to Rust engine.
    Returns a task ID for polling results at /api/v2/compute/jobs/{job_id}.
    """
    valid_methods = ["vanraden1", "vanraden2", "yang"]
    if request.method not in valid_methods:
         # Map legacy or simple names if necessary
         if request.method == "vanraden": request.method = "vanraden1"
         elif request.method not in valid_methods:
            raise HTTPException(status_code=400, detail=f"Invalid method. Choose from: {', '.join(valid_methods)}")

    # Create a job to track status
    job_id = await job_service.create_job(
        job_type="grm",
        metadata={
            "marker_data_id": request.marker_data_id,
            "method": request.method
        }
    )

    # Dispatch to background task
    background_tasks.add_task(_run_grm_job, job_id, request.marker_data_id, request.method)

    return {
        "task_id": job_id,
        "status": "queued",
        "message": "GRM calculation queued. Poll result at /api/v2/compute/jobs/{task_id}",
        "poll_url": f"/api/v2/compute/jobs/{job_id}"
    }


@router.post("/gebv/predict")
async def predict_gebv(request: GEBVRequest, background_tasks: BackgroundTasks):
    """
    Predict Genomic Estimated Breeding Values.
    
    Uses GBLUP or other models via Fortran engine.
    Returns a task ID for polling results.
    """
    if request.model.lower() != "gblup":
         raise HTTPException(status_code=400, detail="Only 'gblup' model is currently supported")

    # Create job
    job_id = await job_service.create_job(
        job_type="gebv",
        metadata={
            "training_data_id": request.training_data_id,
            "trait": request.target_trait,
            "model": request.model
        }
    )

    # Dispatch background task
    background_tasks.add_task(
        _run_gebv_job,
        job_id,
        request.training_data_id,
        request.target_trait,
        request.heritability
    )

    return {
        "task_id": job_id,
        "status": "queued",
        "message": "GEBV prediction queued",
        "poll_url": f"/api/v2/compute/jobs/{job_id}"
    }


@router.get("/ld/{chromosome}")
async def linkage_disequilibrium(chromosome: str, window_kb: int = 100):
    """Get LD decay for a chromosome."""
    return {
        "chromosome": chromosome,
        "window_kb": window_kb,
        "ld_decay": [],
        "r2_threshold": 0.2,
    }


@router.get("/population-structure")
async def population_structure():
    """Get population structure analysis results."""
    return {
        "pca": {"pc1_variance": 0.0, "pc2_variance": 0.0, "coordinates": []},
        "admixture": {"k": 0, "assignments": []},
    }


# =============================================================================
# Background Task Handlers
# =============================================================================

async def _run_grm_job(job_id: str, marker_data_id: str, method: str):
    """
    Background worker for GRM calculation.
    """
    import time
    import asyncio

    try:
        # Update status to running
        await job_service.update_job(job_id, status=JobStatus.RUNNING, progress=0.1)

        # 1. Load Data (Offload to thread)
        def load_data():
            genotypes, sample_ids = genomics_data_service.get_genotypes(marker_data_id)
            return genotypes, sample_ids

        genotypes, sample_ids = await asyncio.to_thread(load_data)
        n_samples, n_markers = genotypes.shape

        await job_service.update_job(job_id, progress=0.3)

        # 2. Compute GRM (Offload to thread)
        start_time = time.time()

        def run_compute():
             return compute_engine.compute_grm(genotypes, method=method)

        result = await asyncio.to_thread(run_compute)
        compute_duration = (time.time() - start_time) * 1000

        # 3. Format Result (convert numpy to list for JSON serialization)
        # For large matrices, we might want to save to file/blob storage instead,
        # but for this API we return inline or summary.

        # We'll return the matrix inline for now as requested by the schema
        # This conversion can also be heavy for large lists
        matrix_list = await asyncio.to_thread(lambda: result.matrix.tolist())

        await job_service.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            result={
                "matrix": matrix_list,
                "sample_ids": sample_ids,
                "n_samples": n_samples,
                "n_markers": n_markers,
                "method": method,
                "compute_time_ms": compute_duration,
                "backend": compute_engine.backend.value
            }
        )

    except Exception as e:
        await job_service.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e)
        )


async def _run_gebv_job(job_id: str, training_data_id: str, trait: str, heritability: float):
    """
    Background worker for GEBV prediction.
    """
    import time
    import asyncio

    try:
        await job_service.update_job(job_id, status=JobStatus.RUNNING, progress=0.1)

        # 1. Load Data (Offload to thread)
        def load_data():
            genotypes, sample_ids = genomics_data_service.get_genotypes(training_data_id)
            phenotypes, pheno_ids = genomics_data_service.get_phenotypes(training_data_id, trait)

            # Ensure dimensions match (simple truncation for simulation)
            n = min(len(phenotypes), genotypes.shape[0])
            genotypes = genotypes[:n, :]
            phenotypes = phenotypes[:n]
            sample_ids = sample_ids[:n]
            return genotypes, phenotypes, sample_ids

        genotypes, phenotypes, sample_ids = await asyncio.to_thread(load_data)

        await job_service.update_job(job_id, progress=0.3)

        # 2. Compute GBLUP (Offload to thread)
        start_time = time.time()

        def run_compute():
            return compute_engine.compute_gblup(genotypes, phenotypes, heritability)

        result = await asyncio.to_thread(run_compute)
        compute_duration = (time.time() - start_time) * 1000

        # 3. Format Result
        breeding_values = await asyncio.to_thread(lambda: result.breeding_values.tolist())

        # Zip with IDs
        gebv_results = [
            {"sample_id": sid, "gebv": bv}
            for sid, bv in zip(sample_ids, breeding_values)
        ]

        await job_service.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            result={
                "gebv_results": gebv_results,
                "fixed_effects": result.fixed_effects.tolist(),
                "compute_time_ms": compute_duration,
                "backend": compute_engine.backend.value
            }
        )

    except Exception as e:
        await job_service.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e)
        )
