"""
Tests for Worker Monitoring API
"""

import pytest
from httpx import AsyncClient

from app.core.redis import redis_client


@pytest.mark.asyncio
async def test_worker_health_endpoint(async_client: AsyncClient):
    """Test worker health endpoint returns valid response"""
    response = await async_client.get("/api/v2/workers/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "workers" in data
    assert "queue_stats" in data
    assert "total_workers" in data
    assert "healthy_workers" in data
    
    # Workers should be a list
    assert isinstance(data["workers"], list)
    
    # Queue stats should be a dict
    assert isinstance(data["queue_stats"], dict)


@pytest.mark.asyncio
async def test_worker_stats_endpoint(async_client: AsyncClient):
    """Test worker stats endpoint returns valid response"""
    response = await async_client.get("/api/v2/workers/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "workers" in data
    assert "total_workers" in data
    
    # Workers should have light, heavy, gpu categories
    assert "light" in data["workers"]
    assert "heavy" in data["workers"]
    assert "gpu" in data["workers"]


@pytest.mark.asyncio
async def test_queue_depth_endpoint_light(async_client: AsyncClient):
    """Test queue depth endpoint for light workers"""
    # Set up some test data in Redis
    await redis_client.connect()
    await redis_client.set(
        "queue:light:stats",
        {
            "total_tasks": 10,
            "pending": 5,
            "running": 2,
            "completed": 3,
            "failed": 0,
            "cancelled": 0,
            "queue_size": 5,
            "max_concurrent": 10,
        },
        ttl_seconds=60
    )
    
    response = await async_client.get("/api/v2/workers/queue/light")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["compute_type"] == "light"
    assert "stats" in data


@pytest.mark.asyncio
async def test_queue_depth_endpoint_invalid_type(async_client: AsyncClient):
    """Test queue depth endpoint with invalid compute type"""
    response = await async_client.get("/api/v2/workers/queue/invalid")
    
    assert response.status_code == 400
    assert "Invalid compute type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_worker_details_endpoint_not_found(async_client: AsyncClient):
    """Test worker details endpoint with non-existent worker"""
    response = await async_client.get("/api/v2/workers/worker/non-existent-worker")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_worker_details_endpoint_with_worker(async_client: AsyncClient):
    """Test worker details endpoint with registered worker"""
    # Register a test worker in Redis
    await redis_client.connect()
    await redis_client.set(
        "worker:light:test-worker-1",
        {
            "worker_id": "test-worker-1",
            "type": "light_python",
            "status": "running",
            "max_concurrent": 10,
            "processed_count": 42,
            "failed_count": 1,
        },
        ttl_seconds=60
    )
    
    response = await async_client.get("/api/v2/workers/worker/test-worker-1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["worker_id"] == "test-worker-1"
    assert data["type"] == "light_python"
    assert data["status"] == "running"
    assert data["processed_count"] == 42
