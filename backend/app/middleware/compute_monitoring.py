"""
Compute Monitoring Middleware
Tracks compute operations with Sentry integration

Features:
- Automatic Sentry transaction tracking for compute jobs
- Domain tagging for compute operations
- Performance monitoring
- Error tracking with context
"""

import time
from typing import Any, Callable

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from app.services.task_queue import ComputeType, Task, TaskStatus


class ComputeMonitor:
    """
    Monitor compute operations and send metrics to Sentry
    
    Usage:
        monitor = ComputeMonitor()
        
        # Track compute job
        with monitor.track_compute_job(job_id, "gwas_analysis", ComputeType.HEAVY_COMPUTE):
            result = await run_gwas(data)
    """
    
    def __init__(self):
        self.enabled = SENTRY_AVAILABLE
    
    def track_compute_job(
        self,
        job_id: str,
        job_name: str,
        compute_type: ComputeType,
        domain: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
    ):
        """
        Context manager to track compute job execution
        
        Args:
            job_id: Unique job identifier
            job_name: Human-readable job name
            compute_type: Type of compute operation
            domain: Domain module (breeding, genomics, etc.)
            user_id: User who submitted the job
            organization_id: Organization context
        
        Example:
            with monitor.track_compute_job(
                job_id="abc123",
                job_name="gwas_analysis",
                compute_type=ComputeType.HEAVY_COMPUTE,
                domain="genomics"
            ):
                result = await run_gwas(data)
        """
        return ComputeJobContext(
            job_id=job_id,
            job_name=job_name,
            compute_type=compute_type,
            domain=domain,
            user_id=user_id,
            organization_id=organization_id,
            enabled=self.enabled,
        )
    
    def record_job_metrics(self, task: Task):
        """
        Record job metrics to Sentry after completion
        
        Args:
            task: Completed task object
        """
        if not self.enabled:
            return
        
        # Calculate execution time
        execution_time = None
        if task.started_at and task.completed_at:
            execution_time = (task.completed_at - task.started_at).total_seconds()
        
        # Set tags
        sentry_sdk.set_tag("compute.job_id", task.id)
        sentry_sdk.set_tag("compute.job_name", task.name)
        sentry_sdk.set_tag("compute.type", task.compute_type.value if task.compute_type else "unknown")
        sentry_sdk.set_tag("compute.status", task.status.value)
        
        if task.metadata.get("domain"):
            sentry_sdk.set_tag("domain", task.metadata["domain"])
        
        # Record metrics
        if execution_time:
            sentry_sdk.set_measurement("compute.execution_time", execution_time, "second")
        
        sentry_sdk.set_measurement("compute.progress", task.progress, "ratio")
        
        # Add breadcrumb
        sentry_sdk.add_breadcrumb(
            category="compute",
            message=f"Compute job {task.status.value}: {task.name}",
            level="info" if task.status == TaskStatus.COMPLETED else "error",
            data={
                "job_id": task.id,
                "job_name": task.name,
                "compute_type": task.compute_type.value if task.compute_type else None,
                "execution_time": execution_time,
                "status": task.status.value,
                "error": task.error,
            },
        )
        
        # Capture error if failed
        if task.status == TaskStatus.FAILED and task.error:
            sentry_sdk.capture_message(
                f"Compute job failed: {task.name}",
                level="error",
                extras={
                    "job_id": task.id,
                    "job_name": task.name,
                    "compute_type": task.compute_type.value if task.compute_type else None,
                    "error": task.error,
                    "execution_time": execution_time,
                },
            )


class ComputeJobContext:
    """Context manager for tracking compute job execution"""
    
    def __init__(
        self,
        job_id: str,
        job_name: str,
        compute_type: ComputeType,
        domain: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        enabled: bool = True,
    ):
        self.job_id = job_id
        self.job_name = job_name
        self.compute_type = compute_type
        self.domain = domain
        self.user_id = user_id
        self.organization_id = organization_id
        self.enabled = enabled
        self.transaction = None
        self.start_time = None
    
    def __enter__(self):
        if not self.enabled:
            return self
        
        self.start_time = time.time()
        
        # Start Sentry transaction
        self.transaction = sentry_sdk.start_transaction(
            op="compute",
            name=f"compute.{self.job_name}",
        )
        
        # Set tags
        sentry_sdk.set_tag("compute.job_id", self.job_id)
        sentry_sdk.set_tag("compute.job_name", self.job_name)
        sentry_sdk.set_tag("compute.type", self.compute_type.value)
        
        if self.domain:
            sentry_sdk.set_tag("domain", self.domain)
        
        if self.user_id:
            sentry_sdk.set_user({"id": self.user_id})
        
        if self.organization_id:
            sentry_sdk.set_tag("organization_id", self.organization_id)
        
        # Add breadcrumb
        sentry_sdk.add_breadcrumb(
            category="compute",
            message=f"Starting compute job: {self.job_name}",
            level="info",
            data={
                "job_id": self.job_id,
                "compute_type": self.compute_type.value,
                "domain": self.domain,
            },
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.enabled:
            return
        
        # Calculate execution time
        execution_time = time.time() - self.start_time if self.start_time else None
        
        # Record execution time
        if execution_time:
            sentry_sdk.set_measurement("compute.execution_time", execution_time, "second")
        
        # Handle errors
        if exc_type is not None:
            sentry_sdk.set_tag("compute.status", "failed")
            sentry_sdk.capture_exception(exc_val)
        else:
            sentry_sdk.set_tag("compute.status", "completed")
        
        # Finish transaction
        if self.transaction:
            self.transaction.finish()


# Global compute monitor instance
compute_monitor = ComputeMonitor()


def wrap_compute_function(
    func: Callable,
    job_name: str,
    compute_type: ComputeType,
    domain: str | None = None,
) -> Callable:
    """
    Decorator to wrap compute functions with monitoring
    
    Args:
        func: Compute function to wrap
        job_name: Human-readable job name
        compute_type: Type of compute operation
        domain: Domain module
    
    Returns:
        Wrapped function with monitoring
    
    Example:
        @wrap_compute_function(
            job_name="gwas_analysis",
            compute_type=ComputeType.HEAVY_COMPUTE,
            domain="genomics"
        )
        async def run_gwas(genotype_data, phenotype_data):
            # Compute logic here
            pass
    """
    async def wrapper(*args, **kwargs):
        job_id = kwargs.get("job_id", "unknown")
        
        with compute_monitor.track_compute_job(
            job_id=job_id,
            job_name=job_name,
            compute_type=compute_type,
            domain=domain,
        ):
            return await func(*args, **kwargs)
    
    return wrapper
