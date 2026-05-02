"""
GWAS PLINK Compute Interface
Wraps PLINK adapter operations in job queue interface

Example usage:
    plink_compute = GWASPlinkCompute()
    job_id = await plink_compute.run_association(bfile, output_prefix, phenotype_file)
    
    # Check status
    status = await plink_compute.get_status(job_id)
    
    # Get result (blocks until complete)
    result = await plink_compute.get_result(job_id)
"""

from pathlib import Path
from typing import Any, Literal

from app.services.compute_interface import BaseComputeInterface, ComputeType, TaskPriority


class GWASPlinkCompute(BaseComputeInterface):
    """
    GWAS PLINK compute interface for genomics domain
    
    Wraps PLINK adapter operations with job queueing,
    timeout handling, and error recovery
    """

    def __init__(self, plink_executable: str = "plink"):
        super().__init__(domain_name="genomics")
        self.plink_executable = plink_executable

    async def run_association(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        phenotype_file: Path | str | None = None,
        covariates_file: Path | str | None = None,
        method: Literal["linear", "logistic", "assoc"] = "linear",
        adjust: bool = False,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue PLINK association analysis job
        
        Args:
            bfile: Input binary file prefix
            output_prefix: Output file prefix
            phenotype_file: Path to phenotype file (optional)
            covariates_file: Path to covariates file (optional)
            method: Association method ('linear', 'logistic', 'assoc')
            adjust: Whether to produce multiple testing adjusted p-values
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        # PLINK operations are typically heavy compute (>30s for large datasets)
        return await self.enqueue(
            compute_name="plink_association",
            compute_func=self._association_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            organization_id=organization_id,
            bfile=bfile,
            output_prefix=output_prefix,
            phenotype_file=phenotype_file,
            covariates_file=covariates_file,
            method=method,
            adjust=adjust,
            plink_executable=self.plink_executable,
        )

    async def calculate_pca(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        n_pcs: int = 10,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue PLINK PCA calculation job
        
        Args:
            bfile: Input binary file prefix
            output_prefix: Output file prefix
            n_pcs: Number of principal components
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        return await self.enqueue(
            compute_name="plink_pca",
            compute_func=self._pca_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.NORMAL,
            user_id=user_id,
            organization_id=organization_id,
            bfile=bfile,
            output_prefix=output_prefix,
            n_pcs=n_pcs,
            plink_executable=self.plink_executable,
        )

    async def ld_pruning(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        window_size: int = 50,
        step_size: int = 5,
        r2_threshold: float = 0.2,
        user_id: str | None = None,
        organization_id: str | None = None,
    ) -> str:
        """
        Queue PLINK LD pruning job
        
        Args:
            bfile: Input binary file prefix
            output_prefix: Output file prefix
            window_size: Window size in SNPs
            step_size: Step size in SNPs
            r2_threshold: r^2 threshold
            user_id: User who submitted the job
            organization_id: Organization context
            
        Returns:
            Job ID for status tracking
        """
        return await self.enqueue(
            compute_name="plink_ld_pruning",
            compute_func=self._ld_pruning_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            priority=TaskPriority.NORMAL,
            user_id=user_id,
            organization_id=organization_id,
            bfile=bfile,
            output_prefix=output_prefix,
            window_size=window_size,
            step_size=step_size,
            r2_threshold=r2_threshold,
            plink_executable=self.plink_executable,
        )

    async def _association_worker(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        phenotype_file: Path | str | None,
        covariates_file: Path | str | None,
        method: str,
        adjust: bool,
        plink_executable: str,
        progress_callback,
    ) -> dict[str, Any]:
        """
        PLINK association worker function
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gwas_plink_adapter import GWASPlinkAdapter

        progress_callback(0.1, f"Initializing PLINK association ({method})")

        try:
            # PLINK operations can take a long time for large datasets
            # Set timeout to 30 minutes
            timeout = 1800
            
            progress_callback(0.3, "Running PLINK association analysis")
            
            adapter = GWASPlinkAdapter(plink_executable=plink_executable)
            
            # Run association with timeout
            result_file = await asyncio.wait_for(
                asyncio.to_thread(
                    adapter.run_association,
                    bfile=bfile,
                    output_prefix=output_prefix,
                    phenotype_file=phenotype_file,
                    covariates_file=covariates_file,
                    method=method,
                    adjust=adjust
                ),
                timeout=timeout
            )
            
            progress_callback(0.8, "Parsing results")
            
            # Parse results
            results_df = await asyncio.to_thread(
                adapter.parse_assoc_results,
                result_file=result_file
            )
            
            progress_callback(1.0, "PLINK association complete")
            
            return {
                "success": True,
                "result_file": str(result_file),
                "n_markers": len(results_df),
                "results": results_df.to_dicts()[:1000],  # Limit to first 1000 for response size
            }

        except asyncio.TimeoutError:
            error_msg = f"PLINK association timed out after {timeout}s"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "result_file": None,
                "n_markers": 0,
                "results": [],
            }
        except Exception as e:
            error_msg = f"PLINK association failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "result_file": None,
                "n_markers": 0,
                "results": [],
            }

    async def _pca_worker(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        n_pcs: int,
        plink_executable: str,
        progress_callback,
    ) -> dict[str, Any]:
        """
        PLINK PCA worker function
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gwas_plink_adapter import GWASPlinkAdapter

        progress_callback(0.1, f"Initializing PLINK PCA (n_pcs={n_pcs})")

        try:
            # PCA can take a long time for large datasets
            # Set timeout to 15 minutes
            timeout = 900
            
            progress_callback(0.3, "Running PLINK PCA")
            
            adapter = GWASPlinkAdapter(plink_executable=plink_executable)
            
            # Run PCA with timeout
            eigenvec_file = await asyncio.wait_for(
                asyncio.to_thread(
                    adapter.calculate_pca,
                    bfile=bfile,
                    output_prefix=output_prefix,
                    n_pcs=n_pcs
                ),
                timeout=timeout
            )
            
            progress_callback(0.8, "Parsing eigenvectors")
            
            # Parse results
            eigenvec_df = await asyncio.to_thread(
                adapter.parse_pca_eigenvec,
                eigenvec_file=eigenvec_file
            )
            
            progress_callback(1.0, "PLINK PCA complete")
            
            return {
                "success": True,
                "eigenvec_file": str(eigenvec_file),
                "n_samples": len(eigenvec_df),
                "n_pcs": n_pcs,
                "eigenvectors": eigenvec_df.to_dicts()[:1000],  # Limit for response size
            }

        except asyncio.TimeoutError:
            error_msg = f"PLINK PCA timed out after {timeout}s"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "eigenvec_file": None,
                "n_samples": 0,
                "n_pcs": 0,
                "eigenvectors": [],
            }
        except Exception as e:
            error_msg = f"PLINK PCA failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "eigenvec_file": None,
                "n_samples": 0,
                "n_pcs": 0,
                "eigenvectors": [],
            }

    async def _ld_pruning_worker(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        window_size: int,
        step_size: int,
        r2_threshold: float,
        plink_executable: str,
        progress_callback,
    ) -> dict[str, Any]:
        """
        PLINK LD pruning worker function
        
        Includes timeout handling and error recovery
        """
        import asyncio
        from app.modules.genomics.compute.analytics.gwas_plink_adapter import GWASPlinkAdapter

        progress_callback(0.1, f"Initializing PLINK LD pruning (r2={r2_threshold})")

        try:
            # LD pruning can take a long time
            # Set timeout to 15 minutes
            timeout = 900
            
            progress_callback(0.3, "Running PLINK LD pruning")
            
            adapter = GWASPlinkAdapter(plink_executable=plink_executable)
            
            # Run LD pruning with timeout
            result_files = await asyncio.wait_for(
                asyncio.to_thread(
                    adapter.ld_pruning,
                    bfile=bfile,
                    output_prefix=output_prefix,
                    window_size=window_size,
                    step_size=step_size,
                    r2_threshold=r2_threshold
                ),
                timeout=timeout
            )
            
            progress_callback(0.8, "Parsing pruned SNPs")
            
            # Parse pruned SNPs
            pruned_snps = await asyncio.to_thread(
                adapter.parse_ld_pruning_results,
                prune_in_file=result_files["prune_in"]
            )
            
            progress_callback(1.0, "PLINK LD pruning complete")
            
            return {
                "success": True,
                "prune_in_file": str(result_files["prune_in"]),
                "prune_out_file": str(result_files["prune_out"]),
                "n_pruned_snps": len(pruned_snps),
                "pruned_snps": pruned_snps[:1000],  # Limit for response size
            }

        except asyncio.TimeoutError:
            error_msg = f"PLINK LD pruning timed out after {timeout}s"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "prune_in_file": None,
                "prune_out_file": None,
                "n_pruned_snps": 0,
                "pruned_snps": [],
            }
        except Exception as e:
            error_msg = f"PLINK LD pruning failed: {str(e)}"
            progress_callback(1.0, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "prune_in_file": None,
                "prune_out_file": None,
                "n_pruned_snps": 0,
                "pruned_snps": [],
            }


# Singleton instance
gwas_plink_compute = GWASPlinkCompute()
