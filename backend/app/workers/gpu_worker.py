"""
GPU Compute Worker
Handles GPU-accelerated operations (WebGPU/CUDA)

Examples:
- Deep learning inference
- Large-scale matrix operations
- Image processing
- Genomic sequence alignment
- Neural network training
"""

import asyncio
import logging
from typing import Any

from app.core.redis import redis_client
from app.services.task_queue import ComputeType, TaskStatus, task_queue


logger = logging.getLogger(__name__)


class GPUComputeWorker:
    """
    GPU compute worker for GPU-accelerated operations
    
    Characteristics:
    - GPU-accelerated (CUDA/WebGPU)
    - Specialized hardware required
    - Very low concurrency (1-2 workers per GPU)
    - High throughput for parallel operations
    """
    
    def __init__(self, worker_id: str = "gpu-worker-1", max_concurrent: int = 1, gpu_id: int = 0):
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        self.gpu_id = gpu_id
        self.running = False
        self.processed_count = 0
        self.failed_count = 0
        self.gpu_available = False
        
    async def start(self):
        """Start the GPU compute worker"""
        logger.info(f"[{self.worker_id}] Starting GPU compute worker (gpu_id={self.gpu_id}, max_concurrent={self.max_concurrent})")
        
        # Check GPU availability
        self.gpu_available = await self._check_gpu_availability()
        
        if not self.gpu_available:
            logger.warning(f"[{self.worker_id}] GPU {self.gpu_id} not available, worker will run in CPU fallback mode")
        
        # Connect to Redis
        await redis_client.connect()
        
        # Start task queue with very low concurrency for GPU operations
        task_queue._max_concurrent = self.max_concurrent
        await task_queue.start()
        
        self.running = True
        
        # Register worker in Redis for monitoring
        await self._register_worker()
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
        
        logger.info(f"[{self.worker_id}] GPU compute worker started")
        
    async def stop(self):
        """Stop the GPU compute worker"""
        logger.info(f"[{self.worker_id}] Stopping GPU compute worker")
        
        self.running = False
        
        # Stop task queue
        await task_queue.stop()
        
        # Unregister worker
        await self._unregister_worker()
        
        # Disconnect from Redis
        await redis_client.disconnect()
        
        logger.info(f"[{self.worker_id}] GPU compute worker stopped")
        
    async def _check_gpu_availability(self) -> bool:
        """Check if GPU is available"""
        try:
            # Try to import CUDA libraries
            import torch
            if torch.cuda.is_available() and torch.cuda.device_count() > self.gpu_id:
                logger.info(f"[{self.worker_id}] GPU {self.gpu_id} available: {torch.cuda.get_device_name(self.gpu_id)}")
                return True
        except ImportError:
            logger.debug(f"[{self.worker_id}] PyTorch not available, checking for other GPU libraries")
        
        # Could add checks for other GPU libraries (TensorFlow, JAX, etc.)
        
        return False
        
    async def _register_worker(self):
        """Register worker in Redis for monitoring"""
        worker_key = f"worker:gpu:{self.worker_id}"
        await redis_client.set(
            worker_key,
            {
                "worker_id": self.worker_id,
                "type": ComputeType.GPU_COMPUTE.value,
                "status": "running",
                "gpu_id": self.gpu_id,
                "gpu_available": self.gpu_available,
                "max_concurrent": self.max_concurrent,
                "processed_count": self.processed_count,
                "failed_count": self.failed_count,
            },
            ttl_seconds=60  # Auto-expire if worker dies
        )
        
    async def _unregister_worker(self):
        """Unregister worker from Redis"""
        worker_key = f"worker:gpu:{self.worker_id}"
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
                    f"queue:gpu:stats",
                    stats,
                    ttl_seconds=60
                )
                
                # Check GPU health if available
                if self.gpu_available:
                    gpu_stats = await self._get_gpu_stats()
                    await redis_client.set(
                        f"worker:gpu:{self.worker_id}:gpu_stats",
                        gpu_stats,
                        ttl_seconds=60
                    )
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"[{self.worker_id}] Health check error: {e}")
                await asyncio.sleep(30)
                
    async def _get_gpu_stats(self) -> dict[str, Any]:
        """Get GPU statistics"""
        try:
            import torch
            if torch.cuda.is_available():
                return {
                    "gpu_id": self.gpu_id,
                    "gpu_name": torch.cuda.get_device_name(self.gpu_id),
                    "memory_allocated": torch.cuda.memory_allocated(self.gpu_id),
                    "memory_reserved": torch.cuda.memory_reserved(self.gpu_id),
                    "memory_total": torch.cuda.get_device_properties(self.gpu_id).total_memory,
                }
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error getting GPU stats: {e}")
        
        return {}
                
    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics"""
        queue_stats = task_queue.get_stats()
        
        return {
            "worker_id": self.worker_id,
            "type": ComputeType.GPU_COMPUTE.value,
            "status": "running" if self.running else "stopped",
            "gpu_id": self.gpu_id,
            "gpu_available": self.gpu_available,
            "max_concurrent": self.max_concurrent,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "queue_stats": queue_stats,
        }


async def run_gpu_worker(worker_id: str = "gpu-worker-1", max_concurrent: int = 1, gpu_id: int = 0):
    """
    Run GPU compute worker
    
    Usage:
        python -m app.workers.gpu_worker
        
    With specific GPU:
        CUDA_VISIBLE_DEVICES=0 python -m app.workers.gpu_worker
    """
    worker = GPUComputeWorker(worker_id=worker_id, max_concurrent=max_concurrent, gpu_id=gpu_id)
    
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
    asyncio.run(run_gpu_worker())
