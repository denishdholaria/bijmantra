"""
GxE Analytics Compute Interface
Wraps GxE interaction scorer operations in job queue interface

Example usage:
    gxe_compute = GxEAnalyticsCompute()
    job_id = await gxe_compute.calculate_all_scores(yield_matrix, genotype_names, environment_names)
    
    # Check status
    status = await gxe_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await gxe_compute.get_result(job_id)
"""

from typing import Any

import numpy as np

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class GxEAnalyticsCompute(BaseComputeInterface):
    """
    GxE analytics compute interface for breeding domain
    
    Wraps GxE interaction scorer operations with job queueing,
    timeout handling, and error recovery
    """

    def __init__(self):
        super().__init__(domain_name="breeding")

    async def calculate_all_scores(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str],
        environment_names: list[str],
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue GxE stability scores calculation job
        
        Args:
            yield_matrix: (n_genotypes, n_environments) yield array
            genotype_names: List of genotype names
            environment_names: List of environment names
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        # Determine compute type based on matrix size
        n_genotypes, n_environments = yield_matrix.shape
        total_cells = n_genotypes * n_environments
        compute_type = ComputeType.HEAVY_COMPUTE if total_cells > 10000 else ComputeType.LIGHT_PYTHON
        
        return await self.enqueue(
            compute_name="gxe_stability_scores",
            compute_func=self._gxe_worker,
            compute_type=compute_type,
            priority=TaskPriority.NORMAL,
            user_id=user_id,
            organization_id=organization_id,
            yield_matrix=yield_matrix,
            genotype_names=genotype_names,
            environment_names=environment_names,
        )

    async def calculate_interaction_matrix(
        self,
        yield_matrix: np.ndarray,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue GxE interaction matrix calculation job
        
        Args:
            yield_matrix: (n_genotypes, n_environments) yield array
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        n_genotypes, n_environments = yield_matrix.shape
        total_cells = n_genotypes * n_environments
        compute_type = ComputeType.HEAVY_COMPUTE if total_cells > 10000 else ComputeType.LIGHT_PYTHON
        
        return await self.enqueue(
            compute_name="gxe_interaction_matrix",
            compute_func=self._interaction_matrix_worker,
            compute_type=compute_type,
            priority=TaskPriority.NORMAL,
            user_id=user_id,
            organization_id=organization_id,
            yield_matrix=yield_matrix,
        )

    async def _gxe_worker(
        self,
        yield_matrix: np.ndarray,
        genotype_names: list[str],
        environment_names: list[str],
        progress_callback,
    ) -> dict[str, Any]:
        """
        GxE worker function (executed by compute workers)
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gxe_interaction_scorer import gxe_interaction_scorer

        n_genotypes, n_environments = yield_matrix.shape
        total_cells = n_genotypes * n_environments
        
        progress_callback(0.1, f"Initializing GxE analysis ({n_genotypes}x{n_environments})")

        try:
            # Set timeout based on matrix size
            # Large matrices (>10k cells) get 5 minutes, otherwise 30 seconds
            timeout = 300 if total_cells > 10000 else 30
            
            progress_callback(0.3, "Calculating stability scores")
            
            # Run scorer with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    gxe_interaction_scorer.calculate_all_scores,
                    yield_matrix=yield_matrix,
                    genotype_names=genotype_names,
                    environment_names=environment_names
                ),
                timeout=timeout
            )
            
            progress_callback(0.9, "Processing results")
            
            # Convert to dictionary
            result_dict = result.to_dict()
            
            progress_callback(1.0, "GxE analysis complete")
            
            return result_dict

        except asyncio.TimeoutError:
            error_msg = f"GxE computation timed out after {timeout}s ({n_genotypes}x{n_environments})"
            progress_callback(1.0, error_msg)
            return {
                "error": error_msg,
                "wricke_ecovalence": {},
                "shukla_stability": {},
                "lin_binns_superiority": {},
                "kang_rank_sum": {},
                "interaction_matrix": [],
                "genotype_names": genotype_names,
                "environment_names": environment_names,
            }
        except Exception as e:
            error_msg = f"GxE computation failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "error": error_msg,
                "wricke_ecovalence": {},
                "shukla_stability": {},
                "lin_binns_superiority": {},
                "kang_rank_sum": {},
                "interaction_matrix": [],
                "genotype_names": genotype_names,
                "environment_names": environment_names,
            }

    async def _interaction_matrix_worker(
        self,
        yield_matrix: np.ndarray,
        progress_callback,
    ) -> dict[str, Any]:
        """
        GxE interaction matrix worker function
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gxe_interaction_scorer import gxe_interaction_scorer

        n_genotypes, n_environments = yield_matrix.shape
        total_cells = n_genotypes * n_environments
        
        progress_callback(0.1, f"Calculating interaction matrix ({n_genotypes}x{n_environments})")

        try:
            # Set timeout based on matrix size
            timeout = 300 if total_cells > 10000 else 30
            
            # Run calculation with timeout
            interaction_matrix = await asyncio.wait_for(
                asyncio.to_thread(
                    gxe_interaction_scorer.calculate_interaction_matrix,
                    yield_matrix=yield_matrix
                ),
                timeout=timeout
            )
            
            progress_callback(1.0, "Interaction matrix complete")
            
            return {
                "interaction_matrix": interaction_matrix.tolist(),
                "shape": list(interaction_matrix.shape),
            }

        except asyncio.TimeoutError:
            error_msg = f"Interaction matrix computation timed out after {timeout}s"
            progress_callback(1.0, error_msg)
            return {
                "error": error_msg,
                "interaction_matrix": [],
                "shape": [0, 0],
            }
        except Exception as e:
            error_msg = f"Interaction matrix computation failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "error": error_msg,
                "interaction_matrix": [],
                "shape": [0, 0],
            }


# Singleton instance
gxe_analytics_compute = GxEAnalyticsCompute()
