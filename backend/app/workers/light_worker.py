"""
Light Compute Worker
Handles Python-only operations (< 30 seconds)

Examples:
- Data validation
- Simple statistics
- Quick transformations
- API data processing
"""

import asyncio
import logging
from typing import Any

from app.core.redis import redis_client
from app.services.task_queue import ComputeType, TaskStatus, task_queue


logger = logging.getLogger(__name__)


class LightComputeWorker:
    """
    Light compute worker for fast Python operations
    
    Characteristics:
    - Python-only (no Rust/Fortran)
    - Expected runtime < 30 seconds
    - High concurrency (many workers)
    - Quick turnaround
    """
    
    def __init__(self, worker_id: str = "light-worker-1", max_concurrent: int = 10):
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        self.running = False
        self.processed_count = 0
        self.failed_count = 0
        
    async def start(self):
        """Start the light compute worker"""
        logger.info(f"[{self.worker_id}] Starting light compute worker (max_concurrent={self.max_concurrent})")
        
        # Connect to Redis
        await redis_client.connect()
        
        # Start task queue with high concurrency
        task_queue._max_concurrent = self.max_concurrent
        await task_queue.start()
        
        self.running = True
        
        # Register worker in Redis for monitoring
        await self._register_worker()
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
        
        logger.info(f"[{self.worker_id}] Light compute worker started")
        
    async def stop(self):
        """Stop the light compute worker"""
        logger.info(f"[{self.worker_id}] Stopping light compute worker")
        
        self.running = False
        
        # Stop task queue
        await task_queue.stop()
        
        # Unregister worker
        await self._unregister_worker()
        
        # Disconnect from Redis
        await redis_client.disconnect()
        
        logger.info(f"[{self.worker_id}] Light compute worker stopped")
        
    async def _register_worker(self):
        """Register worker in Redis for monitoring"""
        worker_key = f"worker:light:{self.worker_id}"
        await redis_client.set(
            worker_key,
            {
                "worker_id": self.worker_id,
                "type": ComputeType.LIGHT_PYTHON.value,
                "status": "running",
                "max_concurrent": self.max_concurrent,
                "processed_count": self.processed_count,
                "failed_count": self.failed_count,
            },
            ttl_seconds=60  # Auto-expire if worker dies
        )
        
    async def _unregister_worker(self):
        """Unregister worker from Redis"""
        worker_key = f"worker:light:{self.worker_id}"
        await redis_client.delete(worker_key)
        
    async def _health_check_loop(self):
        """Periodic health check and metrics update"""
        while self.running:
            try:
                # Update worker status in Redis
                await self._register_worker()
                
                # Update queue metrics
                stats = task_queue.get_stats()
                await redis_client.set(
                    f"queue:light:stats",
                    stats,
                    ttl_seconds=60
                )
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"[{self.worker_id}] Health check error: {e}")
                await asyncio.sleep(30)
                
    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics"""
        queue_stats = task_queue.get_stats()
        
        return {
            "worker_id": self.worker_id,
            "type": ComputeType.LIGHT_PYTHON.value,
            "status": "running" if self.running else "stopped",
            "max_concurrent": self.max_concurrent,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "queue_stats": queue_stats,
        }


async def run_light_worker(worker_id: str = "light-worker-1", max_concurrent: int = 10):
    """
    Run light compute worker
    
    Usage:
        python -m app.workers.light_worker
    """
    worker = LightComputeWorker(worker_id=worker_id, max_concurrent=max_concurrent)
    
    try:
        await worker.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await worker.stop()


if __name__ == "__main__":
    # Run worker
    asyncio.run(run_light_worker())
