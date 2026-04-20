#!/usr/bin/env python3
"""
Worker Monitoring Dashboard
Real-time monitoring of compute worker health and queue depth

Usage:
    python scripts/monitor_workers.py
"""

import asyncio
import sys
from datetime import datetime

from app.core.redis import redis_client
from app.services.task_queue import task_queue


async def get_worker_stats():
    """Get worker statistics from Redis"""
    workers = {
        "light": [],
        "heavy": [],
        "gpu": [],
    }
    
    # Get light workers
    light_keys = await redis_client.keys("worker:light:*")
    for key in light_keys:
        if not key.endswith(":gpu_stats"):
            worker_data = await redis_client.get(key)
            if worker_data:
                workers["light"].append(worker_data)
    
    # Get heavy workers
    heavy_keys = await redis_client.keys("worker:heavy:*")
    for key in heavy_keys:
        if not key.endswith(":gpu_stats"):
            worker_data = await redis_client.get(key)
            if worker_data:
                workers["heavy"].append(worker_data)
    
    # Get GPU workers
    gpu_keys = await redis_client.keys("worker:gpu:*")
    for key in gpu_keys:
        if not key.endswith(":gpu_stats"):
            worker_data = await redis_client.get(key)
            if worker_data:
                workers["gpu"].append(worker_data)
    
    return workers


async def get_queue_stats():
    """Get queue statistics from Redis"""
    stats = {}
    
    for compute_type in ["light", "heavy", "gpu"]:
        queue_stats = await redis_client.get(f"queue:{compute_type}:stats")
        if queue_stats:
            stats[compute_type] = queue_stats
    
    return stats


def print_dashboard(workers, queue_stats):
    """Print monitoring dashboard"""
    # Clear screen
    print("\033[2J\033[H")
    
    # Header
    print("=" * 80)
    print(f"Bijmantra Compute Worker Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Worker summary
    total_workers = sum(len(w) for w in workers.values())
    print(f"Total Workers: {total_workers}")
    print(f"  Light Workers: {len(workers['light'])}")
    print(f"  Heavy Workers: {len(workers['heavy'])}")
    print(f"  GPU Workers: {len(workers['gpu'])}")
    print()
    
    # Light workers
    if workers["light"]:
        print("Light Workers (Python-only, < 30s)")
        print("-" * 80)
        for worker in workers["light"]:
            print(f"  {worker['worker_id']}: {worker['status']} | "
                  f"Processed: {worker['processed_count']} | "
                  f"Failed: {worker['failed_count']} | "
                  f"Max Concurrent: {worker['max_concurrent']}")
        print()
    
    # Heavy workers
    if workers["heavy"]:
        print("Heavy Workers (Rust/Fortran, > 30s)")
        print("-" * 80)
        for worker in workers["heavy"]:
            print(f"  {worker['worker_id']}: {worker['status']} | "
                  f"Processed: {worker['processed_count']} | "
                  f"Failed: {worker['failed_count']} | "
                  f"Max Concurrent: {worker['max_concurrent']}")
        print()
    
    # GPU workers
    if workers["gpu"]:
        print("GPU Workers (WebGPU/CUDA)")
        print("-" * 80)
        for worker in workers["gpu"]:
            gpu_status = "Available" if worker.get("gpu_available") else "Unavailable"
            print(f"  {worker['worker_id']}: {worker['status']} | "
                  f"GPU {worker.get('gpu_id', 0)}: {gpu_status} | "
                  f"Processed: {worker['processed_count']} | "
                  f"Failed: {worker['failed_count']}")
        print()
    
    # Queue statistics
    if queue_stats:
        print("Queue Statistics")
        print("-" * 80)
        for compute_type, stats in queue_stats.items():
            print(f"  {compute_type.upper()} Queue:")
            print(f"    Total Tasks: {stats.get('total_tasks', 0)}")
            print(f"    Pending: {stats.get('pending', 0)} | "
                  f"Running: {stats.get('running', 0)} | "
                  f"Completed: {stats.get('completed', 0)} | "
                  f"Failed: {stats.get('failed', 0)}")
            print(f"    Queue Size: {stats.get('queue_size', 0)}")
        print()
    
    # Footer
    print("=" * 80)
    print("Press Ctrl+C to exit")
    print("=" * 80)


async def monitor_loop():
    """Main monitoring loop"""
    # Connect to Redis
    await redis_client.connect()
    
    try:
        while True:
            # Get worker and queue stats
            workers = await get_worker_stats()
            queue_stats = await get_queue_stats()
            
            # Print dashboard
            print_dashboard(workers, queue_stats)
            
            # Wait 5 seconds before refresh
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    finally:
        await redis_client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        sys.exit(0)
