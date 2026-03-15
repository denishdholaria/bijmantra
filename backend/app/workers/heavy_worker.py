"""
Heavy Compute Worker
Handles Rust/Fortran operations (> 30 seconds)

Examples:
- BLUP/GBLUP calculations
- GWAS analysis
- Genomic relationship matrices
- Large matrix operations
- HPC solver calls
"""

import asyncio
import logging
from typing import Any

from app.core.redis import redis_client
from app.services.task_queue import ComputeType, TaskStatus, task_queue


logger = logging.getLogger(__name__)


class HeavyComputeWorker:
    """
    Heavy compute worker for long-running Rust/Fortran operations
    
    Characteristics:
    - Rust/Fortran compute engines
    - Expected runtime > 30 seconds
    - Lower concurrency (fewer workers)
    - Resource-intensive
    """
    
    def __init__(self, worker_id: str = "heavy-worker-1", max_concurrent: int = 2):
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        self.running = False
        self.processed_count = 0
        self.failed_count = 0
        
    async def start(self):
        """Start the heavy compute worker"""
        logger.info(f"[{self.worker_id}] Starting heavy compute worker (max_concurrent={self.max_concurrent})")
        
        # Connect to Redis
        await redis_client.connect()
        
        # Start task queue with lower concurrency for heavy operations
        task_queue._max_concurrent = self.max_concurrent
        await task_queue.start()
        
        self.running = True
        
        # Register worker in Redis for monitoring
        await self._register_worker()
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
        
        logger.info(f"[{self.worker_id}] Heavy compute worker started")
        
    async def stop(self):
        """Stop the heavy compute worker"""
        logger.info(f"[{self.worker_id}] Stopping heavy compute worker")
        
        self.running = False
        
        # Stop task queue
        await task_queue.stop()
        
        # Unregister worker
        await self._unregister_worker()
        
        # Disconnect from Redis
        await redis_client.disconnect()
        
        logger.info(f"[{self.worker_id}] Heavy compute worker stopped")
        
    async def _register_worker(self):
        """Register worker in Redis for monitoring"""
        worker_key = f"worker:heavy:{self.worker_id}"
        await redis_client.set(
            worker_key,
            {
                "worker_id": self.worker_id,
                "type": ComputeType.HEAVY_COMPUTE.value,
                "status": "running",
                "max_concurrent": self.max_concurrent,
                "processed_count": self.processed_count,
                "failed_count": self.failed_count,
            },
            ttl_seconds=60  # Auto-expire if worker dies
        )
        
    async def _unregister_worker(self):
        """Unregister worker from Redis"""
        worker_key = f"worker:heavy:{self.worker_id}"
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
                    f"queue:heavy:stats",
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
            "type": ComputeType.HEAVY_COMPUTE.value,
            "status": "running" if self.running else "stopped",
            "max_concurrent": self.max_concurrent,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "queue_stats": queue_stats,
        }


async def run_heavy_worker(worker_id: str = "heavy-worker-1", max_concurrent: int = 2):
    """
    Run heavy compute worker
    
    Usage:
        python -m app.workers.heavy_worker
    """
    worker = HeavyComputeWorker(worker_id=worker_id, max_concurrent=max_concurrent)
    
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
    asyncio.run(run_heavy_worker())
