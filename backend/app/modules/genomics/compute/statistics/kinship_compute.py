"""
Kinship Compute Interface
Wraps kinship matrix calculation operations in job queue interface

Example usage:
    kinship_compute = KinshipCompute()
    job_id = await kinship_compute.calculate_vanraden_kinship(genotype_matrix)
    
    # Check status
    status = await kinship_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await kinship_compute.get_result(job_id)
"""

from typing import Any

import numpy as np

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class KinshipCompute(BaseComputeInterface):
    """
    Kinship compute interface for genomics domain
    
    Wraps kinship matrix calculation operations with job queueing,
    timeout handling, and error recovery
    """

    def __init__(self):
        super().__init__(domain_name="genomics")

    async def calculate_vanraden_kinship(
        self,
        genotype_matrix: np.ndarray,
        check_maf: bool = True,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue VanRaden kinship matrix calculation job
        
        Args:
            genotype_matrix: (n_samples x n_markers) matrix
            check_maf: Whether to check minor allele frequency
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        # Determine compute type based on matrix size
        n_samples, n_markers = genotype_matrix.shape
        total_cells = n_samples * n_markers
        compute_type = ComputeType.HEAVY_COMPUTE if total_cells > 100000 else ComputeType.LIGHT_PYTHON
        
        return await self.enqueue(
            compute_name="vanraden_kinship",
            compute_func=self._kinship_worker,
            compute_type=compute_type,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            genotype_matrix=genotype_matrix,
            check_maf=check_maf,
        )

    async def calculate_inbreeding(
        self,
        kinship_matrix: np.ndarray,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue inbreeding coefficient calculation job
        
        Args:
            kinship_matrix: n × n kinship/GRM matrix
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        n = kinship_matrix.shape[0]
        compute_type = ComputeType.HEAVY_COMPUTE if n > 1000 else ComputeType.LIGHT_PYTHON
        
        return await self.enqueue(
            compute_name="inbreeding_coefficients",
            compute_func=self._inbreeding_worker,
            compute_type=compute_type,
            priority=TaskPriority.NORMAL,
            user_id=user_id,
            organization_id=organization_id,
            kinship_matrix=kinship_matrix,
        )

    async def _kinship_worker(
        self,
        genotype_matrix: np.ndarray,
        check_maf: bool,
        progress_callback,
    ) -> dict[str, Any]:
        """
        Kinship worker function (executed by compute workers)
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.statistics.kinship import calculate_vanraden_kinship

        n_samples, n_markers = genotype_matrix.shape
        total_cells = n_samples * n_markers
        
        progress_callback(0.1, f"Initializing kinship calculation ({n_samples}x{n_markers})")

        try:
            # Set timeout based on matrix size
            # Large matrices (>100k cells) get 10 minutes, otherwise 30 seconds
            timeout = 600 if total_cells > 100000 else 30
            
            progress_callback(0.3, "Calculating genomic relationship matrix")
            
            # Run calculation with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    calculate_vanraden_kinship,
                    genotype_matrix=genotype_matrix,
                    check_maf=check_maf
                ),
                timeout=timeout
            )
            
            progress_callback(0.9, "Processing results")
            
            # Check for calculation errors
            if not result.get("success"):
                raise RuntimeError(f"Kinship calculation error: {result.get('error', 'Unknown error')}")
            
            progress_callback(1.0, "Kinship calculation complete")
            
            return result

        except asyncio.TimeoutError:
            error_msg = f"Kinship computation timed out after {timeout}s ({n_samples}x{n_markers})"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "K": [],
                "denominator": 0.0,
                "marker_count": n_markers,
                "sample_count": n_samples,
            }
        except Exception as e:
            error_msg = f"Kinship computation failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "K": [],
                "denominator": 0.0,
                "marker_count": n_markers,
                "sample_count": n_samples,
            }

    async def _inbreeding_worker(
        self,
        kinship_matrix: np.ndarray,
        progress_callback,
    ) -> dict[str, Any]:
        """
        Inbreeding worker function (executed by compute workers)
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.statistics.kinship import calculate_inbreeding

        n = kinship_matrix.shape[0]
        
        progress_callback(0.1, f"Calculating inbreeding coefficients (n={n})")

        try:
            # Set timeout based on matrix size
            timeout = 300 if n > 1000 else 30
            
            # Run calculation with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    calculate_inbreeding,
                    kinship_matrix=kinship_matrix
                ),
                timeout=timeout
            )
            
            progress_callback(0.9, "Processing results")
            
            # Check for calculation errors
            if not result.get("success"):
                raise RuntimeError(f"Inbreeding calculation error: {result.get('error', 'Unknown error')}")
            
            progress_callback(1.0, "Inbreeding calculation complete")
            
            return result

        except asyncio.TimeoutError:
            error_msg = f"Inbreeding computation timed out after {timeout}s (n={n})"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "inbreeding_coefficients": [],
                "average_kinship": [],
                "summary": {},
                "n_individuals": n,
            }
        except Exception as e:
            error_msg = f"Inbreeding computation failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "inbreeding_coefficients": [],
                "average_kinship": [],
                "summary": {},
                "n_individuals": n,
            }


# Singleton instance
kinship_compute = KinshipCompute()
