"""
Monitoring API
Compute layer observability and metrics

Endpoints:
- GET /monitoring/compute - Compute layer metrics
- GET /monitoring/compute/jobs - Job execution metrics
- GET /monitoring/compute/workers - Worker utilization metrics
- GET /monitoring/compute/queue - Queue depth metrics
- GET /monitoring/compute/alerts - Active alerts
- GET /monitoring/dashboard - Web dashboard UI

Metrics tracked:
- Job execution time (P50, P95, P99)
- Job success/failure rate
- Queue depth by worker type
- Worker utilization
- Alert status
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.redis import redis_client
from app.services.task_queue import ComputeType, TaskStatus, task_queue
from app.services.compute_alerting import compute_alerting

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ============================================================================
# Response Models
# ============================================================================


class ComputeMetrics(BaseModel):
    """Overall compute layer metrics"""
    timestamp: datetime
    total_jobs: int
    jobs_pending: int
    jobs_running: int
    jobs_completed: int
    jobs_failed: int
    success_rate: float
    failure_rate: float
    avg_execution_time_seconds: float | None
    queue_depth_total: int
    workers_active: int
    workers_total: int
    worker_utilization: float


class JobExecutionMetrics(BaseModel):
    """Job execution time metrics"""
    timestamp: datetime
    compute_type: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    avg_execution_time_seconds: float | None
    p50_execution_time_seconds: float | None
    p95_execution_time_seconds: float | None
    p99_execution_time_seconds: float | None


class WorkerMetrics(BaseModel):
    """Worker utilization metrics"""
    timestamp: datetime
    worker_type: str
    total_workers: int
    active_workers: int
    utilization: float
    jobs_processed: int
    jobs_failed: int
    max_concurrent: int


class QueueMetrics(BaseModel):
    """Queue depth metrics"""
    timestamp: datetime
    compute_type: str
    queue_depth: int
    pending_jobs: int
    running_jobs: int
    avg_wait_time_seconds: float | None


class Alert(BaseModel):
    """Monitoring alert"""
    id: str
    severity: str  # "warning" | "critical"
    metric: str
    message: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved: bool


class ComputeDashboard(BaseModel):
    """Complete compute monitoring dashboard"""
    timestamp: datetime
    overall_metrics: ComputeMetrics
    job_metrics_by_type: list[JobExecutionMetrics]
    worker_metrics_by_type: list[WorkerMetrics]
    queue_metrics_by_type: list[QueueMetrics]
    active_alerts: list[Alert]


# ============================================================================
# Helper Functions
# ============================================================================


async def get_worker_stats_by_type(compute_type: str) -> dict[str, Any]:
    """Get worker statistics for a specific compute type"""
    workers = []
    
    # Get workers from Redis
    worker_keys = await redis_client.keys(f"worker:{compute_type}:*")
    for key in worker_keys:
        worker_data = await redis_client.get(key)
        if worker_data:
            workers.append(worker_data)
    
    if not workers:
        return {
            "total_workers": 0,
            "active_workers": 0,
            "utilization": 0.0,
            "jobs_processed": 0,
            "jobs_failed": 0,
            "max_concurrent": 0,
        }
    
    total_workers = len(workers)
    active_workers = len([w for w in workers if w.get("status") == "running"])
    jobs_processed = sum(w.get("processed_count", 0) for w in workers)
    jobs_failed = sum(w.get("failed_count", 0) for w in workers)
    max_concurrent = sum(w.get("max_concurrent", 0) for w in workers)
    
    # Calculate utilization (active workers / total workers)
    utilization = active_workers / total_workers if total_workers > 0 else 0.0
    
    return {
        "total_workers": total_workers,
        "active_workers": active_workers,
        "utilization": utilization,
        "jobs_processed": jobs_processed,
        "jobs_failed": jobs_failed,
        "max_concurrent": max_concurrent,
    }


async def get_queue_stats_by_type(compute_type: str) -> dict[str, Any]:
    """Get queue statistics for a specific compute type"""
    queue_stats = await redis_client.get(f"queue:{compute_type}:stats")
    
    if not queue_stats:
        return {
            "queue_depth": 0,
            "pending_jobs": 0,
            "running_jobs": 0,
            "avg_wait_time_seconds": None,
        }
    
    return {
        "queue_depth": queue_stats.get("queue_size", 0),
        "pending_jobs": queue_stats.get("pending", 0),
        "running_jobs": queue_stats.get("running", 0),
        "avg_wait_time_seconds": None,  # TODO: Calculate from job timestamps
    }


def calculate_execution_time_percentiles(jobs: list[dict[str, Any]]) -> dict[str, float | None]:
    """Calculate execution time percentiles from completed jobs"""
    execution_times = []
    
    for job in jobs:
        if job.get("started_at") and job.get("completed_at"):
            started = datetime.fromisoformat(job["started_at"])
            completed = datetime.fromisoformat(job["completed_at"])
            execution_time = (completed - started).total_seconds()
            execution_times.append(execution_time)
    
    if not execution_times:
        return {
            "avg": None,
            "p50": None,
            "p95": None,
            "p99": None,
        }
    
    execution_times.sort()
    n = len(execution_times)
    
    return {
        "avg": sum(execution_times) / n,
        "p50": execution_times[int(n * 0.50)] if n > 0 else None,
        "p95": execution_times[int(n * 0.95)] if n > 1 else None,
        "p99": execution_times[int(n * 0.99)] if n > 2 else None,
    }


def check_alerts(
    overall_metrics: ComputeMetrics,
    job_metrics: list[JobExecutionMetrics],
    queue_metrics: list[QueueMetrics],
) -> list[Alert]:
    """Check for alert conditions based on thresholds"""
    alerts = []
    timestamp = datetime.now(UTC)
    
    # Alert: Compute job failure rate > 5%
    if overall_metrics.failure_rate > 0.05:
        alerts.append(Alert(
            id=f"alert-failure-rate-{timestamp.timestamp()}",
            severity="critical",
            metric="compute_job_failure_rate",
            message=f"Compute job failure rate is {overall_metrics.failure_rate:.1%} (threshold: 5%)",
            threshold=0.05,
            current_value=overall_metrics.failure_rate,
            triggered_at=timestamp,
            resolved=False,
        ))
    
    # Alert: Queue depth > 1000 jobs
    if overall_metrics.queue_depth_total > 1000:
        alerts.append(Alert(
            id=f"alert-queue-depth-overall-{timestamp.timestamp()}",
            severity="warning",
            metric="queue_depth",
            message=f"Total queue depth is {overall_metrics.queue_depth_total} (threshold: 1000)",
            threshold=1000,
            current_value=overall_metrics.queue_depth_total,
            triggered_at=timestamp,
            resolved=False,
        ))

    for queue_metric in queue_metrics:
        if queue_metric.queue_depth > 1000:
            alerts.append(Alert(
                id=f"alert-queue-depth-{queue_metric.compute_type}-{timestamp.timestamp()}",
                severity="warning",
                metric="queue_depth",
                message=f"{queue_metric.compute_type} queue depth is {queue_metric.queue_depth} (threshold: 1000)",
                threshold=1000,
                current_value=queue_metric.queue_depth,
                triggered_at=timestamp,
                resolved=False,
            ))
    
    # Alert: Worker utilization < 20% (underutilized)
    if overall_metrics.worker_utilization < 0.20 and overall_metrics.workers_total > 0:
        alerts.append(Alert(
            id=f"alert-worker-utilization-low-{timestamp.timestamp()}",
            severity="warning",
            metric="worker_utilization",
            message=f"Worker utilization is {overall_metrics.worker_utilization:.1%} (threshold: 20%)",
            threshold=0.20,
            current_value=overall_metrics.worker_utilization,
            triggered_at=timestamp,
            resolved=False,
        ))
    
    # Alert: Worker utilization > 90% (overloaded)
    # Only treat high utilization as overload once there is material backlog.
    if overall_metrics.worker_utilization > 0.90 and overall_metrics.queue_depth_total >= 100:
        alerts.append(Alert(
            id=f"alert-worker-utilization-high-{timestamp.timestamp()}",
            severity="critical",
            metric="worker_utilization",
            message=f"Worker utilization is {overall_metrics.worker_utilization:.1%} (threshold: 90%)",
            threshold=0.90,
            current_value=overall_metrics.worker_utilization,
            triggered_at=timestamp,
            resolved=False,
        ))
    
    return alerts


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_ui():
    """
    Get web-based monitoring dashboard UI
    
    Returns:
        HTML dashboard for viewing compute metrics in a browser
    """
    dashboard_path = Path(__file__).parent.parent / "static" / "compute_dashboard.html"
    
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return HTMLResponse(content=dashboard_path.read_text())


@router.get("/compute", response_model=ComputeDashboard)
async def get_compute_dashboard():
    """
    Get complete compute monitoring dashboard
    
    Returns:
        Complete dashboard with all compute metrics and alerts
    """
    timestamp = datetime.now(UTC)
    
    # Get overall task queue stats
    queue_stats = task_queue.get_stats()
    
    # Calculate success/failure rates
    total_completed = queue_stats["completed"] + queue_stats["failed"]
    success_rate = round(queue_stats["completed"] / total_completed, 2) if total_completed > 0 else 0.0
    failure_rate = round(queue_stats["failed"] / total_completed, 2) if total_completed > 0 else 0.0
    
    # Get worker stats for all types
    light_workers = await get_worker_stats_by_type("light")
    heavy_workers = await get_worker_stats_by_type("heavy")
    gpu_workers = await get_worker_stats_by_type("gpu")
    
    total_workers = light_workers["total_workers"] + heavy_workers["total_workers"] + gpu_workers["total_workers"]
    active_workers = light_workers["active_workers"] + heavy_workers["active_workers"] + gpu_workers["active_workers"]
    worker_utilization = active_workers / total_workers if total_workers > 0 else 0.0
    
    # Overall metrics
    overall_metrics = ComputeMetrics(
        timestamp=timestamp,
        total_jobs=queue_stats["total_tasks"],
        jobs_pending=queue_stats["pending"],
        jobs_running=queue_stats["running"],
        jobs_completed=queue_stats["completed"],
        jobs_failed=queue_stats["failed"],
        success_rate=success_rate,
        failure_rate=failure_rate,
        avg_execution_time_seconds=None,  # TODO: Calculate from job history
        queue_depth_total=queue_stats["queue_size"],
        workers_active=active_workers,
        workers_total=total_workers,
        worker_utilization=worker_utilization,
    )
    
    # Job metrics by type
    job_metrics_by_type = []
    for compute_type in [ComputeType.LIGHT_PYTHON, ComputeType.HEAVY_COMPUTE, ComputeType.GPU_COMPUTE]:
        jobs = task_queue.get_compute_jobs(compute_type=compute_type, limit=1000)
        completed_jobs = [j for j in jobs if j["status"] == TaskStatus.COMPLETED.value]
        failed_jobs = [j for j in jobs if j["status"] == TaskStatus.FAILED.value]
        
        total_jobs = len(jobs)
        completed_count = len(completed_jobs)
        failed_count = len(failed_jobs)
        success_rate = completed_count / (completed_count + failed_count) if (completed_count + failed_count) > 0 else 0.0
        
        # Calculate execution time percentiles
        percentiles = calculate_execution_time_percentiles(completed_jobs)
        
        job_metrics_by_type.append(JobExecutionMetrics(
            timestamp=timestamp,
            compute_type=compute_type.value,
            total_jobs=total_jobs,
            completed_jobs=completed_count,
            failed_jobs=failed_count,
            success_rate=success_rate,
            avg_execution_time_seconds=percentiles["avg"],
            p50_execution_time_seconds=percentiles["p50"],
            p95_execution_time_seconds=percentiles["p95"],
            p99_execution_time_seconds=percentiles["p99"],
        ))
    
    # Worker metrics by type
    worker_metrics_by_type = [
        WorkerMetrics(
            timestamp=timestamp,
            worker_type="light",
            total_workers=light_workers["total_workers"],
            active_workers=light_workers["active_workers"],
            utilization=light_workers["utilization"],
            jobs_processed=light_workers["jobs_processed"],
            jobs_failed=light_workers["jobs_failed"],
            max_concurrent=light_workers["max_concurrent"],
        ),
        WorkerMetrics(
            timestamp=timestamp,
            worker_type="heavy",
            total_workers=heavy_workers["total_workers"],
            active_workers=heavy_workers["active_workers"],
            utilization=heavy_workers["utilization"],
            jobs_processed=heavy_workers["jobs_processed"],
            jobs_failed=heavy_workers["jobs_failed"],
            max_concurrent=heavy_workers["max_concurrent"],
        ),
        WorkerMetrics(
            timestamp=timestamp,
            worker_type="gpu",
            total_workers=gpu_workers["total_workers"],
            active_workers=gpu_workers["active_workers"],
            utilization=gpu_workers["utilization"],
            jobs_processed=gpu_workers["jobs_processed"],
            jobs_failed=gpu_workers["jobs_failed"],
            max_concurrent=gpu_workers["max_concurrent"],
        ),
    ]
    
    # Queue metrics by type
    queue_metrics_by_type = []
    for compute_type in ["light", "heavy", "gpu"]:
        queue_stats = await get_queue_stats_by_type(compute_type)
        queue_metrics_by_type.append(QueueMetrics(
            timestamp=timestamp,
            compute_type=compute_type,
            queue_depth=queue_stats["queue_depth"],
            pending_jobs=queue_stats["pending_jobs"],
            running_jobs=queue_stats["running_jobs"],
            avg_wait_time_seconds=queue_stats["avg_wait_time_seconds"],
        ))
    
    # Check for alerts
    active_alerts = check_alerts(overall_metrics, job_metrics_by_type, queue_metrics_by_type)
    
    return ComputeDashboard(
        timestamp=timestamp,
        overall_metrics=overall_metrics,
        job_metrics_by_type=job_metrics_by_type,
        worker_metrics_by_type=worker_metrics_by_type,
        queue_metrics_by_type=queue_metrics_by_type,
        active_alerts=active_alerts,
    )


@router.get("/compute/jobs", response_model=list[JobExecutionMetrics])
async def get_job_execution_metrics(
    compute_type: Annotated[ComputeType | None, Query(description="Filter by compute type")] = None,
    hours: Annotated[int, Query(description="Time window in hours", ge=1, le=168)] = 24,
):
    """
    Get job execution metrics
    
    Args:
        compute_type: Filter by compute type (light_python, heavy_compute, gpu_compute)
        hours: Time window in hours (default: 24, max: 168)
    
    Returns:
        Job execution metrics including success rate and execution time percentiles
    """
    timestamp = datetime.now(UTC)
    metrics = []
    
    compute_types = [compute_type] if compute_type else [
        ComputeType.LIGHT_PYTHON,
        ComputeType.HEAVY_COMPUTE,
        ComputeType.GPU_COMPUTE,
    ]
    
    for ct in compute_types:
        jobs = task_queue.get_compute_jobs(compute_type=ct, limit=10000)
        
        # Filter by time window
        cutoff = timestamp - timedelta(hours=hours)
        jobs = [
            j for j in jobs
            if datetime.fromisoformat(j["created_at"]) >= cutoff
        ]
        
        completed_jobs = [j for j in jobs if j["status"] == TaskStatus.COMPLETED.value]
        failed_jobs = [j for j in jobs if j["status"] == TaskStatus.FAILED.value]
        
        total_jobs = len(jobs)
        completed_count = len(completed_jobs)
        failed_count = len(failed_jobs)
        success_rate = completed_count / (completed_count + failed_count) if (completed_count + failed_count) > 0 else 0.0
        
        # Calculate execution time percentiles
        percentiles = calculate_execution_time_percentiles(completed_jobs)
        
        metrics.append(JobExecutionMetrics(
            timestamp=timestamp,
            compute_type=ct.value,
            total_jobs=total_jobs,
            completed_jobs=completed_count,
            failed_jobs=failed_count,
            success_rate=success_rate,
            avg_execution_time_seconds=percentiles["avg"],
            p50_execution_time_seconds=percentiles["p50"],
            p95_execution_time_seconds=percentiles["p95"],
            p99_execution_time_seconds=percentiles["p99"],
        ))
    
    return metrics


@router.get("/compute/workers", response_model=list[WorkerMetrics])
async def get_worker_utilization_metrics():
    """
    Get worker utilization metrics
    
    Returns:
        Worker metrics for all compute types including utilization and job counts
    """
    timestamp = datetime.now(UTC)
    metrics = []
    
    for worker_type in ["light", "heavy", "gpu"]:
        worker_stats = await get_worker_stats_by_type(worker_type)
        
        metrics.append(WorkerMetrics(
            timestamp=timestamp,
            worker_type=worker_type,
            total_workers=worker_stats["total_workers"],
            active_workers=worker_stats["active_workers"],
            utilization=worker_stats["utilization"],
            jobs_processed=worker_stats["jobs_processed"],
            jobs_failed=worker_stats["jobs_failed"],
            max_concurrent=worker_stats["max_concurrent"],
        ))
    
    return metrics


@router.get("/compute/queue", response_model=list[QueueMetrics])
async def get_queue_depth_metrics():
    """
    Get queue depth metrics
    
    Returns:
        Queue metrics for all compute types including depth and wait times
    """
    timestamp = datetime.now(UTC)
    metrics = []
    
    for compute_type in ["light", "heavy", "gpu"]:
        queue_stats = await get_queue_stats_by_type(compute_type)
        
        metrics.append(QueueMetrics(
            timestamp=timestamp,
            compute_type=compute_type,
            queue_depth=queue_stats["queue_depth"],
            pending_jobs=queue_stats["pending_jobs"],
            running_jobs=queue_stats["running_jobs"],
            avg_wait_time_seconds=queue_stats["avg_wait_time_seconds"],
        ))
    
    return metrics


@router.get("/compute/alerts", response_model=list[Alert])
async def get_active_alerts():
    """
    Get active monitoring alerts
    
    Returns:
        List of active alerts based on threshold violations
    """
    # Trigger alert check
    triggered_alerts = await compute_alerting.check_alerts()
    
    # Get alert history (last 24 hours)
    alert_history = await compute_alerting.get_alert_history(hours=24)
    
    # Convert to Alert models
    alerts = []
    for alert_data in alert_history:
        alerts.append(Alert(
            id=alert_data["id"],
            severity=alert_data["severity"],
            metric=alert_data["metric"],
            message=alert_data["message"],
            threshold=alert_data["threshold"],
            current_value=alert_data["current_value"],
            triggered_at=datetime.fromisoformat(alert_data["triggered_at"]),
            resolved=False,  # TODO: Implement alert resolution
        ))
    
    return alerts


@router.post("/compute/alerts/check")
async def trigger_alert_check():
    """
    Manually trigger alert check
    
    Returns:
        List of newly triggered alerts
    """
    alerts = await compute_alerting.check_alerts()
    
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "alerts_triggered": len(alerts),
        "alerts": alerts,
    }


@router.get("/compute/alerts/history")
async def get_alert_history(
    hours: int = Query(24, description="Time window in hours", ge=1, le=168),
):
    """
    Get alert history
    
    Args:
        hours: Time window in hours (default: 24, max: 168)
    
    Returns:
        List of historical alerts
    """
    alert_history = await compute_alerting.get_alert_history(hours=hours)
    
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "time_window_hours": hours,
        "total_alerts": len(alert_history),
        "alerts": alert_history,
    }
