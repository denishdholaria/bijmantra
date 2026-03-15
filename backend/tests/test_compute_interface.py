"""
Tests for Compute Interface Pattern
"""

import asyncio

import numpy as np
import pytest

from app.modules.breeding.compute import BLUPCompute
from app.modules.genomics.compute import GWASCompute
from app.services.task_queue import ComputeType, TaskStatus, task_queue


@pytest.fixture(autouse=True)
async def setup_task_queue():
    """Start task queue before each test"""
    await task_queue.start()
    yield
    await task_queue.stop()
    # Clear tasks
    task_queue._tasks.clear()


@pytest.mark.asyncio
async def test_gwas_compute_interface():
    """Test GWAS compute interface"""
    gwas_compute = GWASCompute()

    # Create test data
    genotype_data = np.random.randint(0, 3, size=(100, 1000))
    phenotype_data = np.random.randn(100)

    # Submit job
    job_id = await gwas_compute.run_gwas(
        genotype_data=genotype_data,
        phenotype_data=phenotype_data,
        method="linear",
        user_id="test_user",
    )

    assert job_id is not None
    assert isinstance(job_id, str)

    # Check status
    status = await gwas_compute.get_status(job_id)
    assert status is not None
    assert status["id"] == job_id
    assert status["name"] == "genomics.gwas_analysis"
    assert status["compute_type"] == ComputeType.HEAVY_COMPUTE.value

    # Wait for completion
    await asyncio.sleep(0.5)

    # Get result
    result = await gwas_compute.get_result(job_id)
    assert result is not None
    assert "method" in result
    assert result["method"] == "linear"
    assert result["n_samples"] == 100
    assert result["n_markers"] == 1000


@pytest.mark.asyncio
async def test_blup_compute_interface():
    """Test BLUP compute interface"""
    blup_compute = BLUPCompute()

    # Create test data
    n = 50
    p = 2
    q = 50
    phenotypes = np.random.randn(n)
    fixed_effects = np.random.randn(n, p)
    random_effects = np.eye(n)
    relationship_matrix_inv = np.eye(q)
    var_additive = 1.0
    var_residual = 1.0

    # Submit job
    job_id = await blup_compute.run_blup(
        phenotypes=phenotypes,
        fixed_effects=fixed_effects,
        random_effects=random_effects,
        relationship_matrix_inv=relationship_matrix_inv,
        var_additive=var_additive,
        var_residual=var_residual,
        user_id="test_user",
    )

    assert job_id is not None

    # Check status
    status = await blup_compute.get_status(job_id)
    assert status is not None
    assert status["name"] == "breeding.blup_estimation"
    assert status["compute_type"] == ComputeType.HEAVY_COMPUTE.value

    # Wait for completion
    await asyncio.sleep(0.5)

    # Get result
    result = await blup_compute.get_result(job_id)
    assert result is not None
    assert "fixed_effects" in result
    assert "breeding_values" in result
    assert result["converged"] is True


@pytest.mark.asyncio
async def test_gblup_compute_interface():
    """Test GBLUP compute interface"""
    blup_compute = BLUPCompute()

    # Create test data
    genotypes = np.random.randint(0, 3, size=(50, 1000))
    phenotypes = np.random.randn(50)

    # Submit job
    job_id = await blup_compute.run_gblup(
        genotypes=genotypes,
        phenotypes=phenotypes,
        heritability=0.5,
        user_id="test_user",
    )

    assert job_id is not None

    # Check status
    status = await blup_compute.get_status(job_id)
    assert status is not None
    assert status["name"] == "breeding.gblup_estimation"

    # Wait for completion
    await asyncio.sleep(0.5)

    # Get result
    result = await blup_compute.get_result(job_id)
    assert result is not None
    assert "breeding_values" in result


@pytest.mark.asyncio
async def test_compute_job_listing():
    """Test listing compute jobs"""
    gwas_compute = GWASCompute()

    # Submit multiple jobs
    genotype_data = np.random.randint(0, 3, size=(50, 500))
    phenotype_data = np.random.randn(50)

    job_ids = []
    for i in range(3):
        job_id = await gwas_compute.run_gwas(
            genotype_data=genotype_data,
            phenotype_data=phenotype_data,
            user_id=f"user_{i}",
        )
        job_ids.append(job_id)

    # List all jobs
    jobs = gwas_compute.get_jobs(limit=10)
    assert len(jobs) >= 3

    # Filter by compute type
    heavy_jobs = gwas_compute.get_jobs(compute_type=ComputeType.HEAVY_COMPUTE)
    assert len(heavy_jobs) >= 3

    # Filter by user
    user_jobs = gwas_compute.get_jobs(user_id="user_0")
    assert len(user_jobs) >= 1


@pytest.mark.asyncio
async def test_compute_job_cancellation():
    """Test cancelling compute jobs"""
    gwas_compute = GWASCompute()

    # Submit job
    genotype_data = np.random.randint(0, 3, size=(50, 500))
    phenotype_data = np.random.randn(50)

    job_id = await gwas_compute.run_gwas(
        genotype_data=genotype_data,
        phenotype_data=phenotype_data,
    )

    # Cancel immediately (before it starts)
    cancelled = await gwas_compute.cancel(job_id)
    assert cancelled is True

    # Check status
    status = await gwas_compute.get_status(job_id)
    assert status["status"] == TaskStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_compute_job_error_handling():
    """Test error handling in compute jobs"""
    gwas_compute = GWASCompute()

    # Try to get status of non-existent job
    status = await gwas_compute.get_status("non_existent_job")
    assert status is None

    # Try to get result of non-existent job
    with pytest.raises(ValueError):
        await gwas_compute.get_result("non_existent_job")


@pytest.mark.asyncio
async def test_task_queue_compute_methods():
    """Test task queue compute-specific methods"""
    # Submit a compute job directly via task queue
    async def dummy_compute(data, progress_callback):
        progress_callback(0.5, "Processing")
        await asyncio.sleep(0.1)
        progress_callback(1.0, "Done")
        return {"result": data * 2}

    job_id = await task_queue.enqueue_compute(
        compute_name="test_compute",
        compute_func=dummy_compute,
        compute_type=ComputeType.LIGHT_PYTHON,
        data=42,
    )

    assert job_id is not None

    # Get status
    status = await task_queue.get_compute_status(job_id)
    assert status is not None
    assert status["compute_type"] == ComputeType.LIGHT_PYTHON.value

    # Wait for completion
    await asyncio.sleep(0.5)

    # Get result
    result = await task_queue.get_compute_result(job_id)
    assert result == {"result": 84}

    # Get compute jobs
    jobs = task_queue.get_compute_jobs(compute_type=ComputeType.LIGHT_PYTHON)
    assert len(jobs) >= 1
