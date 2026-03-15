"""
Background Task Queue API
Long-running operations management
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.task_queue import Task, TaskStatus, task_queue


router = APIRouter(prefix="/tasks", tags=["Task Queue"], dependencies=[Depends(get_current_user)])


# Response Models
class TaskResponse(BaseModel):
    """Task response"""

    id: str
    name: str
    status: str
    priority: int
    progress: float
    progress_message: str
    result: Any | None = None
    error: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    user_id: str | None = None
    organization_id: str | None = None
    metadata: dict[str, Any] = {}


class TaskStatsResponse(BaseModel):
    """Task queue statistics"""

    total_tasks: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    queue_size: int
    max_concurrent: int


def _task_to_response(task: Task) -> TaskResponse:
    """Convert Task to response"""
    return TaskResponse(
        id=task.id,
        name=task.name,
        status=task.status.value,
        priority=task.priority.value,
        progress=task.progress,
        progress_message=task.progress_message,
        result=task.result,
        error=task.error,
        created_at=task.created_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        user_id=task.user_id,
        organization_id=task.organization_id,
        metadata=task.metadata,
    )


# Endpoints
@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status: str | None = None,
    user_id: str | None = None,
    limit: int = 100,
):
    """List all tasks"""
    # Parse status if provided
    parsed_status = None
    if status:
        try:
            parsed_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    tasks = task_queue.get_tasks(
        status=parsed_status,
        user_id=user_id,
        limit=limit,
    )

    return [_task_to_response(t) for t in tasks]


@router.get("/stats", response_model=TaskStatsResponse)
async def get_stats():
    """Get task queue statistics"""
    return task_queue.get_stats()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a pending task"""
    if not task_queue.cancel_task(task_id):
        raise HTTPException(
            status_code=400, detail="Task not found or cannot be cancelled (not pending)"
        )
    return {"message": "Task cancelled"}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed/failed/cancelled task"""
    if not task_queue.delete_task(task_id):
        raise HTTPException(status_code=400, detail="Task not found or still running")
    return {"message": "Task deleted"}


@router.post("/cleanup")
async def cleanup_tasks(max_age_hours: int = 24):
    """Remove old completed/failed tasks"""
    removed = task_queue.cleanup_old_tasks(max_age_hours)
    return {"message": f"Removed {removed} old tasks"}
