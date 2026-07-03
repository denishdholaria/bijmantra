"""
BLUP Compute Interface
Best Linear Unbiased Prediction compute operations

Example usage:
    blup_compute = BLUPCompute()
    job_id = await blup_compute.run_blup(phenotypes, fixed_effects, random_effects)
    
    # Check status
    status = await blup_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await blup_compute.get_result(job_id)
"""

from typing import Any

import numpy as np

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class BLUPCompute(BaseComputeInterface):
    """
    BLUP compute interface for breeding domain

    Provides job queueing for BLUP/GBLUP breeding value estimation
    """

    def __init__(self):
        super().__init__(domain_name="breeding")

    async def run_blup(
        self,
        phenotypes: np.ndarray,
        fixed_effects: np.ndarray,
        random_effects: np.ndarray,
        relationship_matrix_inv: np.ndarray,
        var_additive: float,
        var_residual: float,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue BLUP computation job

        Args:
            phenotypes: Phenotypic observations (n,)
            fixed_effects: Fixed effects design matrix (n, p)
            random_effects: Random effects design matrix (n, q)
            relationship_matrix_inv: Inverse of relationship matrix (q, q)
            var_additive: Additive genetic variance
            var_residual: Residual variance
            user_id: User who submitted the job
            organization_id: Organization context

        Returns:
            Job ID for status tracking
        """
        return await self.enqueue(
            compute_name="blup_estimation",
            compute_func=self._blup_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            phenotypes=phenotypes,
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            relationship_matrix_inv=relationship_matrix_inv,
            var_additive=var_additive,
            var_residual=var_residual,
        )

    async def run_gblup(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        heritability: float = 0.5,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue GBLUP computation job

        Args:
            genotypes: Marker genotype matrix (n, m), coded as 0, 1, 2
            phenotypes: Phenotypic observations (n,)
            heritability: Heritability estimate (0-1)
            user_id: User who submitted the job
            organization_id: Organization context

        Returns:
            Job ID for status tracking
        """
        return await self.enqueue(
            compute_name="gblup_estimation",
            compute_func=self._gblup_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            genotypes=genotypes,
            phenotypes=phenotypes,
            heritability=heritability,
        )

    async def _blup_worker(
        self,
        phenotypes: np.ndarray,
        fixed_effects: np.ndarray,
        random_effects: np.ndarray,
        relationship_matrix_inv: np.ndarray,
        var_additive: float,
        var_residual: float,
        progress_callback,
    ) -> dict[str, Any]:
        """
        BLUP worker function (executed by compute workers)

        Uses compute_engine for heavy Fortran/Rust operations
        """
        from app.services.compute_engine import compute_engine

        progress_callback(0.1, "Initializing BLUP computation")

        # Use compute_engine for heavy operations
        result = compute_engine.compute_blup(
            phenotypes=phenotypes,
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            relationship_matrix_inv=relationship_matrix_inv,
            var_additive=var_additive,
            var_residual=var_residual,
        )

        progress_callback(1.0, "BLUP computation complete")

        return {
            "fixed_effects": result.fixed_effects.tolist(),
            "breeding_values": result.breeding_values.tolist(),
            "reliability": result.reliability.tolist() if result.reliability is not None else None,
            "converged": result.converged,
            "iterations": result.iterations,
        }

    async def _gblup_worker(
        self,
        genotypes: np.ndarray,
        phenotypes: np.ndarray,
        heritability: float,
        progress_callback,
    ) -> dict[str, Any]:
        """
        GBLUP worker function (executed by compute workers)

        Uses compute_engine for heavy Fortran/Rust operations
        """
        from app.services.compute_engine import compute_engine

        progress_callback(0.1, "Initializing GBLUP computation")

        # Use compute_engine for heavy operations
        result = compute_engine.compute_gblup(
            genotypes=genotypes,
            phenotypes=phenotypes,
            heritability=heritability,
        )

        progress_callback(1.0, "GBLUP computation complete")

        return {
            "fixed_effects": result.fixed_effects.tolist(),
            "breeding_values": result.breeding_values.tolist(),
            "reliability": result.reliability.tolist() if result.reliability is not None else None,
            "converged": result.converged,
            "iterations": result.iterations,
        }
