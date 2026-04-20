"""
Example: Using the Compute Interface Pattern

This example demonstrates how to use the compute interface pattern
for queueing heavy compute operations across domains.
"""

import asyncio

import numpy as np

from app.modules.breeding.compute import BLUPCompute
from app.modules.genomics.compute import GWASCompute
from app.services.task_queue import task_queue


async def example_gwas_analysis():
    """Example: GWAS analysis using compute interface"""
    print("\n=== GWAS Analysis Example ===")

    # Initialize compute interface
    gwas_compute = GWASCompute()

    # Create sample data
    n_samples = 100
    n_markers = 1000
    genotype_data = np.random.randint(0, 3, size=(n_samples, n_markers))
    phenotype_data = np.random.randn(n_samples)

    print(f"Submitting GWAS job with {n_samples} samples and {n_markers} markers...")

    # Submit job
    job_id = await gwas_compute.run_gwas(
        genotype_data=genotype_data,
        phenotype_data=phenotype_data,
        method="linear",
        user_id="example_user",
    )

    print(f"Job submitted: {job_id}")

    # Check status
    status = await gwas_compute.get_status(job_id)
    print(f"Job status: {status['status']}")
    print(f"Progress: {status['progress'] * 100:.1f}%")

    # Wait for completion
    print("Waiting for job to complete...")
    result = await gwas_compute.get_result(job_id)

    print(f"Job completed!")
    print(f"Method: {result['method']}")
    print(f"Samples: {result['n_samples']}")
    print(f"Markers: {result['n_markers']}")


async def example_blup_estimation():
    """Example: BLUP estimation using compute interface"""
    print("\n=== BLUP Estimation Example ===")

    # Initialize compute interface
    blup_compute = BLUPCompute()

    # Create sample data
    n = 50
    p = 2
    q = 50
    phenotypes = np.random.randn(n)
    fixed_effects = np.random.randn(n, p)
    random_effects = np.eye(n)
    relationship_matrix_inv = np.eye(q)
    var_additive = 1.0
    var_residual = 1.0

    print(f"Submitting BLUP job with {n} observations...")

    # Submit job
    job_id = await blup_compute.run_blup(
        phenotypes=phenotypes,
        fixed_effects=fixed_effects,
        random_effects=random_effects,
        relationship_matrix_inv=relationship_matrix_inv,
        var_additive=var_additive,
        var_residual=var_residual,
        user_id="example_user",
    )

    print(f"Job submitted: {job_id}")

    # Check status
    status = await blup_compute.get_status(job_id)
    print(f"Job status: {status['status']}")

    # Wait for completion
    print("Waiting for job to complete...")
    result = await blup_compute.get_result(job_id)

    print(f"Job completed!")
    print(f"Converged: {result['converged']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Fixed effects: {result['fixed_effects'][:3]}...")
    print(f"Breeding values: {result['breeding_values'][:3]}...")


async def example_gblup_estimation():
    """Example: GBLUP estimation using compute interface"""
    print("\n=== GBLUP Estimation Example ===")

    # Initialize compute interface
    blup_compute = BLUPCompute()

    # Create sample data
    n_samples = 50
    n_markers = 1000
    genotypes = np.random.randint(0, 3, size=(n_samples, n_markers))
    phenotypes = np.random.randn(n_samples)

    print(f"Submitting GBLUP job with {n_samples} samples and {n_markers} markers...")

    # Submit job
    job_id = await blup_compute.run_gblup(
        genotypes=genotypes,
        phenotypes=phenotypes,
        heritability=0.5,
        user_id="example_user",
    )

    print(f"Job submitted: {job_id}")

    # Check status
    status = await blup_compute.get_status(job_id)
    print(f"Job status: {status['status']}")

    # Wait for completion
    print("Waiting for job to complete...")
    result = await blup_compute.get_result(job_id)

    print(f"Job completed!")
    print(f"Converged: {result['converged']}")
    print(f"Breeding values: {result['breeding_values'][:5]}...")


async def example_job_listing():
    """Example: Listing compute jobs"""
    print("\n=== Job Listing Example ===")

    gwas_compute = GWASCompute()

    # Submit multiple jobs
    genotype_data = np.random.randint(0, 3, size=(50, 500))
    phenotype_data = np.random.randn(50)

    print("Submitting 3 GWAS jobs...")
    job_ids = []
    for i in range(3):
        job_id = await gwas_compute.run_gwas(
            genotype_data=genotype_data,
            phenotype_data=phenotype_data,
            user_id=f"user_{i}",
        )
        job_ids.append(job_id)
        print(f"  Job {i+1}: {job_id}")

    # List all jobs
    print("\nListing all jobs:")
    jobs = gwas_compute.get_jobs(limit=10)
    for job in jobs:
        print(f"  {job['id'][:8]}... - {job['name']} - {job['status']}")

    # Filter by user
    print("\nListing jobs for user_0:")
    user_jobs = gwas_compute.get_jobs(user_id="user_0")
    for job in user_jobs:
        print(f"  {job['id'][:8]}... - {job['name']} - {job['status']}")


async def main():
    """Run all examples"""
    print("Starting Compute Interface Pattern Examples")
    print("=" * 50)

    # Start task queue
    await task_queue.start()

    try:
        # Run examples
        await example_gwas_analysis()
        await example_blup_estimation()
        await example_gblup_estimation()
        await example_job_listing()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    finally:
        # Stop task queue
        await task_queue.stop()


if __name__ == "__main__":
    asyncio.run(main())
