"""
Compute Interface Pattern
Base class for domain-specific compute operations

This module provides a consistent interface for queueing compute jobs
across all domains (breeding, genomics, phenotyping, etc.)

Usage:
    from app.services.compute_interface import BaseComputeInterface, ComputeType
    from app.services.task_queue import task_queue

    class GWASCompute(BaseComputeInterface):
        async def run_gwas(self, genotype_data, phenotype_data):
            job_id = await self.enqueue(
                "gwas_analysis",
                self._gwas_worker,
                compute_type=ComputeType.HEAVY_COMPUTE,
                genotype_data=genotype_data,
                phenotype_data=phenotype_data
            )
            return job_id

        async def _gwas_worker(self, genotype_data, phenotype_data, progress_callback):
            # Heavy compute logic here
            result = perform_gwas(genotype_data, phenotype_data)
            return result
"""

from typing import Any

from app.services.task_queue import ComputeType, TaskPriority, task_queue


class BaseComputeInterface:
    """
    Base class for domain-specific compute interfaces

    Provides consistent methods for:
    - Queueing compute jobs
    - Tracking job status
    - Retrieving results

    Each domain should subclass this and implement domain-specific
    compute methods that use enqueue() to submit jobs.
    """

    def __init__(self, domain_name: str):
        """
        Initialize compute interface

        Args:
            domain_name: Name of the domain (e.g., "genomics", "breeding")
        """
        self.domain_name = domain_name
        self.task_queue = task_queue

    async def enqueue(
        self,
        compute_name: str,
        compute_func,
        compute_type: ComputeType = ComputeType.LIGHT_PYTHON,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str | None = None,
        organization_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Enqueue a compute job

        Args:
            compute_name: Name of the compute operation
            compute_func: Async function to execute
            compute_type: Type of compute for worker routing
            priority: Job priority level
            user_id: User who submitted the job
            organization_id: Organization context
            **kwargs: Arguments to pass to compute_func

        Returns:
            Job ID for status tracking
        """
        full_name = f"{self.domain_name}.{compute_name}"
        return await self.task_queue.enqueue_compute(
            compute_name=full_name,
            compute_func=compute_func,
            compute_type=compute_type,
            priority=priority,
            user_id=user_id,
            organization_id=organization_id,
            **kwargs,
        )

    async def get_status(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job status and progress

        Args:
            job_id: Job ID returned from enqueue

        Returns:
            Dictionary with job status, progress, and metadata
        """
        return await self.task_queue.get_compute_status(job_id)

    async def get_result(self, job_id: str) -> Any:
        """
        Get job result (blocks until completed)

        Args:
            job_id: Job ID returned from enqueue

        Returns:
            Compute result if completed
            Raises exception if job failed
        """
        return await self.task_queue.get_compute_result(job_id)

    async def cancel(self, job_id: str) -> bool:
        """
        Cancel a pending job

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if job not found or already running
        """
        return self.task_queue.cancel_task(job_id)

    def get_jobs(
        self,
        compute_type: ComputeType | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get compute jobs for this domain

        Args:
            compute_type: Filter by compute type
            user_id: Filter by user
            limit: Maximum number of jobs to return

        Returns:
            List of job status dictionaries
        """
        return self.task_queue.get_compute_jobs(
            compute_type=compute_type,
            user_id=user_id,
            limit=limit,
        )
