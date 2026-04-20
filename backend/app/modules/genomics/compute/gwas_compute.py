"""
GWAS Compute Interface
Genome-Wide Association Study compute operations

Example usage:
    gwas_compute = GWASCompute()
    job_id = await gwas_compute.run_gwas(genotype_data, phenotype_data)
    
    # Check status
    status = await gwas_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await gwas_compute.get_result(job_id)
"""

from typing import Any

import numpy as np
from scipy import stats

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class GWASCompute(BaseComputeInterface):
    """
    GWAS compute interface for genomics domain

    Provides job queueing for GWAS analysis operations
    """

    def __init__(self):
        super().__init__(domain_name="genomics")

    @staticmethod
    def _coerce_design_matrix(covariates: np.ndarray | None, n_samples: int) -> np.ndarray:
        """Build the base regression design matrix with intercept and optional covariates."""
        intercept = np.ones((n_samples, 1), dtype=np.float64)

        if covariates is None:
            return intercept

        covariate_matrix = np.asarray(covariates, dtype=np.float64)
        if covariate_matrix.ndim == 1:
            covariate_matrix = covariate_matrix.reshape(-1, 1)

        if covariate_matrix.shape[0] != n_samples:
            raise ValueError(
                "Covariates must have the same number of rows as genotype and phenotype samples."
            )

        return np.column_stack((intercept, covariate_matrix))

    @staticmethod
    def _linear_marker_scan(
        marker_vector: np.ndarray,
        phenotype_vector: np.ndarray,
        base_design: np.ndarray,
    ) -> tuple[float, float]:
        """Run a single-marker ordinary least squares association test."""
        x = np.asarray(marker_vector, dtype=np.float64)
        y = np.asarray(phenotype_vector, dtype=np.float64)

        valid_mask = np.isfinite(x) & np.isfinite(y) & np.all(np.isfinite(base_design), axis=1)
        if valid_mask.sum() <= base_design.shape[1] + 1:
            return 1.0, 0.0

        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        base_valid = base_design[valid_mask]

        if np.nanstd(x_valid) < 1e-12:
            return 1.0, 0.0

        design = np.column_stack((base_valid, x_valid))
        beta, _, _, _ = np.linalg.lstsq(design, y_valid, rcond=None)
        fitted = design @ beta
        residuals = y_valid - fitted
        dof = y_valid.shape[0] - design.shape[1]

        effect = float(beta[-1])
        if dof <= 0:
            return 1.0, effect

        rss = float(np.dot(residuals, residuals))
        sigma_sq = rss / dof if rss > 0 else 0.0
        if sigma_sq <= 0:
            return 1.0, effect

        xtx_inv = np.linalg.pinv(design.T @ design)
        se = float(np.sqrt(max(sigma_sq * xtx_inv[-1, -1], 0.0)))
        if se <= 0:
            return 1.0, effect

        t_stat = effect / se
        p_value = float(2 * stats.t.sf(abs(t_stat), dof))
        return p_value, effect

    async def run_gwas(
        self,
        genotype_data: np.ndarray,
        phenotype_data: np.ndarray,
        covariates: np.ndarray | None = None,
        method: str = "linear",
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue GWAS analysis job

        Args:
            genotype_data: Genotype matrix (n_samples x n_markers)
            phenotype_data: Phenotype vector (n_samples,)
            covariates: Optional covariate matrix (n_samples x n_covariates)
            method: GWAS method ("linear", "logistic", "mixed")
            user_id: User who submitted the job
            organization_id: Organization context

        Returns:
            Job ID for status tracking
        """
        return await self.enqueue(
            compute_name="gwas_analysis",
            compute_func=self._gwas_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            genotype_data=genotype_data,
            phenotype_data=phenotype_data,
            covariates=covariates,
            method=method,
        )

    async def _gwas_worker(
        self,
        genotype_data: np.ndarray,
        phenotype_data: np.ndarray,
        covariates: np.ndarray | None,
        method: str,
        progress_callback,
    ) -> dict[str, Any]:
        """GWAS worker function using an explicit linear marker scan."""

        genotype_matrix = np.asarray(genotype_data, dtype=np.float64)
        phenotype_vector = np.asarray(phenotype_data, dtype=np.float64)
        n_samples, n_markers = genotype_matrix.shape

        if phenotype_vector.shape[0] != n_samples:
            raise ValueError(
                "Phenotype vector length must match genotype sample count for GWAS analysis."
            )

        supported_methods = {"linear", "mixed"}
        if method not in supported_methods:
            raise ValueError(
                f"Unsupported GWAS method '{method}'. Supported methods: {sorted(supported_methods)}"
            )

        base_design = self._coerce_design_matrix(covariates, n_samples)
        p_values: list[float] = []
        effect_sizes: list[float] = []

        progress_callback(0.1, "Initializing GWAS analysis")

        report_stride = max(1, n_markers // 10)
        for marker_index in range(n_markers):
            p_value, effect = self._linear_marker_scan(
                genotype_matrix[:, marker_index],
                phenotype_vector,
                base_design,
            )
            p_values.append(p_value)
            effect_sizes.append(effect)

            if marker_index == 0 or (marker_index + 1) % report_stride == 0 or marker_index == n_markers - 1:
                progress = 0.1 + (0.8 * (marker_index + 1) / n_markers)
                progress_callback(progress, f"Analyzed {marker_index + 1} of {n_markers} markers")

        progress_callback(0.9, "Finalizing results")

        significant_markers = [
            {
                "marker_index": marker_index,
                "p_value": p_value,
                "effect_size": effect_sizes[marker_index],
            }
            for marker_index, p_value in enumerate(p_values)
            if p_value < 0.05
        ]
        significant_markers.sort(key=lambda marker: marker["p_value"])

        result = {
            "method": method,
            "n_samples": n_samples,
            "n_markers": n_markers,
            "p_values": p_values,
            "effect_sizes": effect_sizes,
            "significant_markers": significant_markers,
        }

        progress_callback(1.0, "GWAS analysis complete")

        return result
