"""
Worker Monitoring API
Endpoints for monitoring compute worker health and queue depth
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.redis import redis_client
from app.services.task_queue import ComputeType, task_queue


router = APIRouter(prefix="/workers", tags=["workers"])


class WorkerStatus(BaseModel):
    """Worker status response"""
    worker_id: str
    type: str
    status: str
    max_concurrent: int
    processed_count: int
    failed_count: int


class QueueStats(BaseModel):
    """Queue statistics response"""
    total_tasks: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    queue_size: int
    max_concurrent: int


class WorkerHealthResponse(BaseModel):
    """Worker health response"""
    workers: list[WorkerStatus]
    queue_stats: dict[str, QueueStats]
    total_workers: int
    healthy_workers: int


@router.get("/health", response_model=WorkerHealthResponse)
async def get_worker_health() -> WorkerHealthResponse:
    """
    Get worker health status and queue depth
    
    Returns:
        Worker health information including:
        - Active workers by type
        - Queue statistics
        - Worker health status
    """
    workers = []
    queue_stats = {}
    
    # Get light workers
    light_worker_keys = await redis_client.keys("worker:light:*")
    for key in light_worker_keys:
        worker_data = await redis_client.get(key)
        if worker_data:
            workers.append(WorkerStatus(**worker_data))
    
    # Get heavy workers
    heavy_worker_keys = await redis_client.keys("worker:heavy:*")
    for key in heavy_worker_keys:
        worker_data = await redis_client.get(key)
        if worker_data:
            workers.append(WorkerStatus(**worker_data))
    
    # Get GPU workers
    gpu_worker_keys = await redis_client.keys("worker:gpu:*")
    for key in gpu_worker_keys:
        worker_data = await redis_client.get(key)
        if worker_data:
            workers.append(WorkerStatus(**worker_data))
    
    # Get queue statistics
    for compute_type in ["light", "heavy", "gpu"]:
        stats_data = await redis_client.get(f"queue:{compute_type}:stats")
        if stats_data:
            queue_stats[compute_type] = QueueStats(**stats_data)
    
    # Count healthy workers (registered in last 60 seconds)
    healthy_workers = len(workers)
    
    return WorkerHealthResponse(
        workers=workers,
        queue_stats=queue_stats,
        total_workers=len(workers),
        healthy_workers=healthy_workers,
    )


@router.get("/stats")
async def get_worker_stats() -> dict[str, Any]:
    """
    Get detailed worker statistics
    
    Returns:
        Detailed statistics including:
        - Worker counts by type
        - Queue depth by type
        - Processing rates
        - Error rates
    """
    # Get all workers
    light_workers = await redis_client.keys("worker:light:*")
    heavy_workers = await redis_client.keys("worker:heavy:*")
    gpu_workers = await redis_client.keys("worker:gpu:*")
    
    # Get queue stats
    light_stats = await redis_client.get("queue:light:stats") or {}
    heavy_stats = await redis_client.get("queue:heavy:stats") or {}
    gpu_stats = await redis_client.get("queue:gpu:stats") or {}
    
    return {
        "workers": {
            "light": {
                "count": len(light_workers),
                "queue_stats": light_stats,
            },
            "heavy": {
                "count": len(heavy_workers),
                "queue_stats": heavy_stats,
            },
            "gpu": {
                "count": len(gpu_workers),
                "queue_stats": gpu_stats,
            },
        },
        "total_workers": len(light_workers) + len(heavy_workers) + len(gpu_workers),
    }


@router.get("/queue/{compute_type}")
async def get_queue_depth(compute_type: str) -> dict[str, Any]:
    """
    Get queue depth for a specific compute type
    
    Args:
        compute_type: Type of compute (light, heavy, gpu)
    
    Returns:
        Queue depth and statistics
    """
    if compute_type not in ["light", "heavy", "gpu"]:
        raise HTTPException(status_code=400, detail="Invalid compute type")
    
    stats = await redis_client.get(f"queue:{compute_type}:stats")
    
    if not stats:
        raise HTTPException(status_code=404, detail=f"No statistics found for {compute_type} queue")
    
    return {
        "compute_type": compute_type,
        "stats": stats,
    }


@router.get("/worker/{worker_id}")
async def get_worker_details(worker_id: str) -> dict[str, Any]:
    """
    Get details for a specific worker
    
    Args:
        worker_id: Worker identifier
    
    Returns:
        Worker details and statistics
    """
    # Try to find worker in all types
    for worker_type in ["light", "heavy", "gpu"]:
        worker_key = f"worker:{worker_type}:{worker_id}"
        worker_data = await redis_client.get(worker_key)
        
        if worker_data:
            # Get GPU stats if GPU worker
            if worker_type == "gpu":
                gpu_stats = await redis_client.get(f"{worker_key}:gpu_stats")
                if gpu_stats:
                    worker_data["gpu_stats"] = gpu_stats
            
            return worker_data
    
    raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
