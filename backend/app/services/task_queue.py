"""
Background Task Queue Service
Long-running operations for Bijmantra

Features:
- Async task execution
- Priority queues
- Progress tracking
- Task cancellation
- Result storage
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, UTC
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import traceback


class TaskStatus(str, Enum):
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


@dataclass
class Task:
    """Background task"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    progress_message: str = ""
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """
    Background task queue for long-running operations
    
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
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._workers: List[asyncio.Task] = []
        self._running = False
    
    async def start(self):
        """Start the task queue workers"""
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        print(f"[TaskQueue] Started {self._max_concurrent} workers")
    
    async def stop(self):
        """Stop the task queue"""
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        self._workers.clear()
        print("[TaskQueue] Stopped")
    
    async def _worker(self, worker_id: int):
        """Worker coroutine that processes tasks"""
        while self._running:
            try:
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
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[TaskQueue] Worker {worker_id} error: {e}")
    
    async def _execute_task(self, task: Task, worker_id: int):
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        self._running_count += 1
        
        print(f"[TaskQueue] Worker {worker_id} executing: {task.name}")
        
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
            print(f"[TaskQueue] Task {task.id} failed: {e}")
        
        finally:
            task.completed_at = datetime.now(UTC)
            self._running_count -= 1
    
    async def submit(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Submit a task to the queue"""
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
        
        # Add to priority queue (negative priority for max-heap behavior)
        await self._queue.put((-priority.value, task_id))
        
        print(f"[TaskQueue] Submitted: {name} (id={task_id[:8]})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        tasks = list(self._tasks.values())
        
        return {
            "total_tasks": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": self._running_count,
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
            "queue_size": self._queue.qsize(),
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


# Global task queue instance
task_queue = TaskQueue()
