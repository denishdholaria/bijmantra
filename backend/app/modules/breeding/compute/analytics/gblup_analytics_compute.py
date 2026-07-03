"""
GBLUP Analytics Compute Interface
Wraps GBLUP matrix solver operations in job queue interface

Example usage:
    gblup_compute = GBLUPAnalyticsCompute()
    job_id = await gblup_compute.solve_gblup(phenotypes, g_matrix, heritability)
    
    # Check status
    status = await gblup_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await gblup_compute.get_result(job_id)
"""

from typing import Any

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class GBLUPAnalyticsCompute(BaseComputeInterface):
    """
    GBLUP analytics compute interface for breeding domain
    
    Wraps GBLUP matrix solver operations with job queueing,
    timeout handling, and error recovery
    """

    def __init__(self):
        super().__init__(domain_name="breeding")

    async def solve_gblup(
        self,
        phenotypes: list[float],
        g_matrix: list[list[float]],
        heritability: float,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue GBLUP matrix solver job
        
        Args:
            phenotypes: Vector of phenotypic values
            g_matrix: Genomic relationship matrix (G)
            heritability: Narrow-sense heritability (h^2), must be in (0, 1]
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        # Determine compute type based on matrix size
        n = len(phenotypes)
        compute_type = ComputeType.HEAVY_COMPUTE if n > 1000 else ComputeType.LIGHT_PYTHON
        
        return await self.enqueue(
            compute_name="gblup_matrix_solver",
            compute_func=self._gblup_worker,
            compute_type=compute_type,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            phenotypes=phenotypes,
            g_matrix=g_matrix,
            heritability=heritability,
        )

    async def _gblup_worker(
        self,
        phenotypes: list[float],
        g_matrix: list[list[float]],
        heritability: float,
        progress_callback,
    ) -> dict[str, Any]:
        """
        GBLUP worker function (executed by compute workers)
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gblup_matrix_solver import GBLUPMatrixSolver

        progress_callback(0.1, "Initializing GBLUP solver")

        try:
            # Set timeout for operations > 30 seconds
            # For large matrices (n > 1000), allow up to 5 minutes
            n = len(phenotypes)
            timeout = 300 if n > 1000 else 30
            
            progress_callback(0.3, f"Solving GBLUP equations (n={n})")
            
            # Run solver with timeout
            solver = GBLUPMatrixSolver()
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    solver.solve,
                    phenotypes=phenotypes,
                    g_matrix=g_matrix,
                    heritability=heritability
                ),
                timeout=timeout
            )
            
            progress_callback(0.9, "Processing results")
            
            # Check for solver errors
            if result.get("error"):
                raise RuntimeError(f"GBLUP solver error: {result['error']}")
            
            progress_callback(1.0, "GBLUP computation complete")
            
            return result

        except asyncio.TimeoutError:
            error_msg = f"GBLUP computation timed out after {timeout}s (n={n})"
            progress_callback(1.0, error_msg)
            return {
                "gebv": [],
                "reliability": [],
                "genetic_variance": 0.0,
                "error_variance": 0.0,
                "mean": 0.0,
                "heritability": heritability,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"GBLUP computation failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "gebv": [],
                "reliability": [],
                "genetic_variance": 0.0,
                "error_variance": 0.0,
                "mean": 0.0,
                "heritability": heritability,
                "error": error_msg
            }


# Singleton instance
gblup_analytics_compute = GBLUPAnalyticsCompute()
