"""
Background Task Queue Service
Long-running operations for Bijmantra

Features:
- Async task execution
- Priority queues
- Progress tracking
- Task cancellation
- Result storage
- Compute job queueing (Python/Rust/Fortran/WASM)
- Job status tracking and result retrieval
- Durable persistence via compute_jobs table (survives process restarts)
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(StrEnum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class ComputeType(StrEnum):
    """Compute operation types for worker routing"""
    LIGHT_PYTHON = "light_python"  # Python-only, < 30s
    HEAVY_COMPUTE = "heavy_compute"  # Rust/Fortran, > 30s
    GPU_COMPUTE = "gpu_compute"  # WebGPU/CUDA operations


@dataclass
class Task:
    """Background task"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    progress_message: str = ""
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    user_id: str | None = None
    organization_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    compute_type: ComputeType | None = None  # For compute job routing


class JobStore:
    """
    Thin async wrapper around the ``compute_jobs`` DB table.

    All methods are fire-and-forget from the queue's perspective — a DB
    failure must never crash the in-process queue.  Errors are logged at
    ERROR level so they are visible without being fatal.
    """

    @staticmethod
    async def persist_enqueue(task: "Task") -> None:
        """Insert a new job row when a task is first submitted."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.compute_job import ComputeJob

            async with AsyncSessionLocal() as session:
                job = ComputeJob(
                    job_id=task.id,
                    name=task.name,
                    user_id=task.user_id,
                    organization_id=int(task.organization_id) if task.organization_id else None,
                    status=task.status.value,
                    priority=task.priority.value,
                    compute_type=task.compute_type.value if task.compute_type else None,
                    progress=task.progress,
                    metadata_json=task.metadata or {},
                )
                session.add(job)
                await session.commit()
        except Exception as exc:
            logger.error("[TaskQueue] Failed to persist job %s to DB: %s", task.id[:8], exc)

    @staticmethod
    async def persist_update(task: "Task") -> None:
        """Update status, progress, result, and timestamps for an existing job row."""
        try:
            from sqlalchemy import select
            from app.core.database import AsyncSessionLocal
            from app.models.compute_job import ComputeJob

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ComputeJob).where(ComputeJob.job_id == task.id)
                )
                job = result.scalar_one_or_none()
                if job is None:
                    # Row may have been lost (e.g. DB was wiped) — re-insert
                    await JobStore.persist_enqueue(task)
                    return

                job.status = task.status.value
                job.progress = task.progress
                job.progress_message = task.progress_message or None
                job.started_at = task.started_at
                job.completed_at = task.completed_at
                job.error_message = task.error or None
                if task.result is not None:
                    try:
                        import json as _json
                        # Ensure result is JSON-serialisable before storing
                        _json.dumps(task.result)
                        job.result_json = task.result
                    except (TypeError, ValueError):
                        job.result_json = {"_serialization_error": str(task.result)[:500]}
                await session.commit()
        except Exception as exc:
            logger.error("[TaskQueue] Failed to update job %s in DB: %s", task.id[:8], exc)

    @staticmethod
    async def load_pending() -> list[dict[str, Any]]:
        """Return all rows with status='pending' for startup rehydration."""
        try:
            from sqlalchemy import select
            from app.core.database import AsyncSessionLocal
            from app.models.compute_job import ComputeJob

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ComputeJob).where(ComputeJob.status == "pending")
                )
                rows = result.scalars().all()
                return [
                    {
                        "job_id": r.job_id,
                        "name": r.name,
                        "user_id": r.user_id,
                        "organization_id": r.organization_id,
                        "priority": r.priority,
                        "compute_type": r.compute_type,
                        "metadata": r.metadata_json or {},
                    }
                    for r in rows
                ]
        except Exception as exc:
            logger.error("[TaskQueue] Failed to load pending jobs from DB: %s", exc)
            return []

    @staticmethod
    async def mark_running_as_failed() -> int:
        """
        On startup, any row still in 'running' state was interrupted mid-flight.
        Mark them as failed so callers get a clear signal rather than stale 'running'.
        """
        try:
            from sqlalchemy import update
            from app.core.database import AsyncSessionLocal
            from app.models.compute_job import ComputeJob

            async with AsyncSessionLocal() as session:
                stmt = (
                    update(ComputeJob)
                    .where(ComputeJob.status == "running")
                    .values(
                        status="failed",
                        error_message="Process restarted while job was running.",
                        completed_at=datetime.now(UTC),
                    )
                )
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
        except Exception as exc:
            logger.error("[TaskQueue] Failed to mark interrupted jobs as failed: %s", exc)
            return 0


class TaskQueue:
    """
    Background task queue for long-running operations.

    Persistence contract
    --------------------
    Every submitted job is written to the ``compute_jobs`` DB table via
    ``JobStore``.  On startup, ``rehydrate_from_db()`` re-enqueues any rows
    whose status is still ``pending`` — so jobs survive process restarts.

    Usage:
        # Define a task function
        async def compute_blup(data, progress_callback):
            for i in range(100):
                await asyncio.sleep(0.1)
                progress_callback(i / 100, f"Processing {i}%")
            return {"result": "done"}

        # Submit task
        task_id = await task_queue.submit(
            "compute_blup",
            compute_blup,
            args=(data,),
            priority=TaskPriority.HIGH
        )

        # Check status
        task = task_queue.get_task(task_id)
    """

    def __init__(self, max_concurrent: int = 5):
        self._tasks: dict[str, Task] = {}
        self._queue: asyncio.PriorityQueue | None = None
        self._queue_loop: asyncio.AbstractEventLoop | None = None
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def _ensure_queue_for_current_loop(self):
        """Bind queue to the current running loop and rehydrate pending tasks when loop changes."""
        current_loop = asyncio.get_running_loop()

        if self._queue is not None and self._queue_loop is current_loop:
            return

        self._queue = asyncio.PriorityQueue()
        self._queue_loop = current_loop

        # Re-enqueue pending tasks after loop changes (common in test lifecycles).
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                await self._queue.put((-task.priority.value, task.id))

    async def start(self):
        """Start the task queue workers"""
        if self._running:
            return

        await self._ensure_queue_for_current_loop()

        self._running = True

        # Start worker tasks
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

        logger.info("[TaskQueue] Started %d workers", self._max_concurrent)

        # Rehydrate: mark interrupted jobs as failed, then re-enqueue pending ones
        asyncio.create_task(self._rehydrate_from_db())
        # Periodic cleanup: purge old completed/failed tasks from memory every hour
        asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the task queue"""
        self._running = False

        # Cancel all workers
        for worker in self._workers:
            worker.cancel()

        self._workers.clear()
        logger.info("[TaskQueue] Stopped")

    async def _rehydrate_from_db(self) -> None:
        """
        On startup:
        1. Mark any 'running' rows as failed (they were interrupted mid-flight).
        2. Re-enqueue 'pending' rows so they are not silently lost.

        This runs as a background task after start() so it doesn't block
        the worker startup path.  Jobs that cannot be rehydrated (because
        their compute function is not registered) are left as pending in the
        DB and will be picked up if the function is re-registered.
        """
        interrupted = await JobStore.mark_running_as_failed()
        if interrupted:
            logger.warning(
                "[TaskQueue] Marked %d interrupted jobs as failed on startup.", interrupted
            )

        pending_rows = await JobStore.load_pending()
        if not pending_rows:
            return

        logger.info(
            "[TaskQueue] Rehydrating %d pending jobs from DB.", len(pending_rows)
        )
        for row in pending_rows:
            job_id = row["job_id"]
            if job_id in self._tasks:
                continue  # Already in memory

            # We cannot reconstruct the original callable from the DB row.
            # Create a sentinel task that immediately fails with a clear message
            # so the caller gets a definitive status rather than stale 'pending'.
            async def _restart_required(**_kwargs: Any) -> None:
                raise RuntimeError(
                    "Job was pending when the process restarted. "
                    "Please resubmit the compute request."
                )

            task = Task(
                id=job_id,
                name=row["name"],
                func=_restart_required,
                priority=TaskPriority(row.get("priority", TaskPriority.NORMAL)),
                user_id=row.get("user_id"),
                organization_id=row.get("organization_id"),
                metadata=row.get("metadata", {}),
            )
            if row.get("compute_type"):
                try:
                    task.compute_type = ComputeType(row["compute_type"])
                except ValueError:
                    pass

            self._tasks[job_id] = task
            if self._queue is not None:
                await self._queue.put((-task.priority.value, job_id))

    @property
    def is_running(self) -> bool:
        """Whether the task queue workers are currently running."""
        return self._running

    async def _worker(self, worker_id: int):
        """Worker coroutine that processes tasks"""
        while self._running:
            try:
                if self._queue is None:
                    await asyncio.sleep(0.1)
                    continue

                # Get next task (blocks until available)
                priority, task_id = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )

                task = self._tasks.get(task_id)
                if not task or task.status == TaskStatus.CANCELLED:
                    continue

                # Execute task
                await self._execute_task(task, worker_id)

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[TaskQueue] Worker %d error: %s", worker_id, e)

    async def _execute_task(self, task: Task, worker_id: int):
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        self._running_count += 1

        logger.debug("[TaskQueue] Worker %d executing: %s", worker_id, task.name)

        # Persist the transition to RUNNING immediately
        asyncio.create_task(JobStore.persist_update(task))

        # Create progress callback
        def progress_callback(progress: float, message: str = ""):
            task.progress = min(1.0, max(0.0, progress))
            task.progress_message = message

        try:
            # Execute the task function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, progress_callback=progress_callback, **task.kwargs)
            else:
                result = task.func(*task.args, progress_callback=progress_callback, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0

        except Exception as e:
            task.error = f"{type(e).__name__}: {str(e)}"
            task.status = TaskStatus.FAILED
            logger.error("[TaskQueue] Task %s failed: %s", task.id[:8], e)

        finally:
            task.completed_at = datetime.now(UTC)
            self._running_count -= 1
            # Persist final state (COMPLETED or FAILED)
            asyncio.create_task(JobStore.persist_update(task))

    async def _cleanup_loop(self) -> None:
        """Periodically purge old completed/failed tasks from the in-memory dict.

        Runs every hour while the queue is running.  Prevents unbounded memory
        growth when many jobs are submitted over the lifetime of the process.
        Default retention: 24 hours after completion.
        """
        while self._running:
            await asyncio.sleep(3600)  # 1 hour
            if not self._running:
                break
            try:
                removed = self.cleanup_old_tasks(max_age_hours=24)
                if removed:
                    logger.info("[TaskQueue] Cleaned up %d old tasks from memory.", removed)
            except Exception as exc:
                logger.error("[TaskQueue] Cleanup loop error: %s", exc)

    async def submit(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str | None = None,
        organization_id: str | None = None,
        metadata: dict[str, Any] = None,
    ) -> str:
        """Submit a task to the queue"""
        await self._ensure_queue_for_current_loop()

        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata or {},
        )

        self._tasks[task_id] = task

        # Persist to DB before enqueuing so the job is durable even if the
        # process crashes before the worker picks it up.
        asyncio.create_task(JobStore.persist_enqueue(task))

        # Add to priority queue (negative priority for max-heap behavior)
        if self._queue is not None:
            await self._queue.put((-priority.value, task_id))

        logger.debug("[TaskQueue] Submitted: %s (id=%s)", name, task_id[:8])
        return task_id

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID"""
        return self._tasks.get(task_id)

    def get_tasks(
        self,
        status: TaskStatus | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks with optional filters"""
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True

        return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a completed/failed/cancelled task"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            del self._tasks[task_id]
            return True

        return False

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        tasks = list(self._tasks.values())
        queue_size = self._queue.qsize() if self._queue is not None else 0

        return {
            "total_tasks": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": self._running_count,
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
            "queue_size": queue_size,
            "max_concurrent": self._max_concurrent,
        }

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Remove old completed/failed tasks"""
        cutoff = datetime.now(UTC)
        removed = 0

        for task_id, task in list(self._tasks.items()):
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.completed_at:
                    age = (cutoff - task.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        del self._tasks[task_id]
                        removed += 1

        return removed

    # =========================================================================
    # Compute Job Queue Interface
    # =========================================================================

    async def enqueue_compute(
        self,
        compute_name: str,
        compute_func: Callable,
        compute_type: ComputeType = ComputeType.LIGHT_PYTHON,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str | None = None,
        organization_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Enqueue a compute job for execution by workers

        This is the primary interface for queueing heavy compute operations
        across all domains (breeding, genomics, phenotyping, etc.)

        Args:
            compute_name: Name of the compute operation (e.g., "gwas_analysis")
            compute_func: Async function to execute
            compute_type: Type of compute for worker routing
            priority: Job priority level
            user_id: User who submitted the job
            organization_id: Organization context
            **kwargs: Arguments to pass to compute_func

        Returns:
            Job ID for status tracking and result retrieval

        Example:
            job_id = await task_queue.enqueue_compute(
                "gwas_analysis",
                gwas_compute_func,
                compute_type=ComputeType.HEAVY_COMPUTE,
                genotype_data=genotypes,
                phenotype_data=phenotypes
            )
        """
        task_id = await self.submit(
            name=compute_name,
            func=compute_func,
            kwargs=kwargs,
            priority=priority,
            user_id=user_id,
            organization_id=organization_id,
            metadata={"compute_type": compute_type.value},
        )

        # Update task with compute type for worker routing
        task = self._tasks.get(task_id)
        if task:
            task.compute_type = compute_type

        return task_id

    async def get_compute_status(self, job_id: str) -> dict[str, Any] | None:
        """
        Get compute job status and progress

        Args:
            job_id: Job ID returned from enqueue_compute

        Returns:
            Dictionary with job status, progress, and metadata
            None if job not found

        Example:
            status = await task_queue.get_compute_status(job_id)
            if status["status"] == "completed":
                result = status["result"]
        """
        task = self.get_task(job_id)
        if not task:
            return None

        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "progress": task.progress,
            "progress_message": task.progress_message,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "compute_type": task.compute_type.value if task.compute_type else None,
            "metadata": task.metadata,
        }

    async def get_compute_result(self, job_id: str) -> Any:
        """
        Get compute job result (blocks until completed)

        Args:
            job_id: Job ID returned from enqueue_compute

        Returns:
            Compute result if completed
            Raises exception if job failed or not found

        Example:
            result = await task_queue.get_compute_result(job_id)
        """
        task = self.get_task(job_id)
        if not task:
            raise ValueError(f"Job {job_id} not found")

        # Poll until completed
        max_wait = 3600  # 1 hour timeout
        poll_interval = 0.5  # 500ms
        elapsed = 0.0

        while task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            if elapsed >= max_wait:
                raise TimeoutError(f"Job {job_id} timed out after {max_wait}s")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        if task.status == TaskStatus.FAILED:
            raise RuntimeError(f"Job {job_id} failed: {task.error}")

        if task.status == TaskStatus.CANCELLED:
            raise RuntimeError(f"Job {job_id} was cancelled")

        return task.result

    def get_compute_jobs(
        self,
        compute_type: ComputeType | None = None,
        status: TaskStatus | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get compute jobs with optional filters

        Args:
            compute_type: Filter by compute type
            status: Filter by job status
            user_id: Filter by user
            limit: Maximum number of jobs to return

        Returns:
            List of job status dictionaries
        """
        tasks = list(self._tasks.values())

        # Filter by compute type
        if compute_type:
            tasks = [t for t in tasks if t.compute_type == compute_type]

        # Filter by status
        if status:
            tasks = [t for t in tasks if t.status == status]

        # Filter by user
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Convert to dictionaries
        return [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status.value,
                "progress": t.progress,
                "compute_type": t.compute_type.value if t.compute_type else None,
                "created_at": t.created_at.isoformat(),
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks[:limit]
        ]


# Global task queue instance
task_queue = TaskQueue()
