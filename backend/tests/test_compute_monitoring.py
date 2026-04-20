"""
Tests for Compute Monitoring Dashboard
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v2.monitoring import (
    get_compute_dashboard,
    get_job_execution_metrics,
    get_worker_utilization_metrics,
    get_queue_depth_metrics,
    get_active_alerts,
)
from app.services.task_queue import ComputeType, TaskStatus


@pytest.fixture
def mock_task_queue():
    """Mock task queue with sample data"""
    with patch("app.api.v2.monitoring.task_queue") as mock:
        mock.get_stats.return_value = {
            "total_tasks": 100,
            "pending": 10,
            "running": 5,
            "completed": 80,
            "failed": 5,
            "cancelled": 0,
            "queue_size": 15,
            "max_concurrent": 10,
        }
        
        mock.get_compute_jobs.return_value = [
            {
                "id": "job1",
                "name": "test_job",
                "status": TaskStatus.COMPLETED.value,
                "compute_type": ComputeType.LIGHT_PYTHON.value,
                "created_at": datetime.now(UTC).isoformat(),
                "started_at": datetime.now(UTC).isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
            }
        ]
        
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch("app.api.v2.monitoring.redis_client") as mock:
        mock.keys = AsyncMock(return_value=[])
        mock.get = AsyncMock(return_value=None)
        yield mock


@pytest.mark.asyncio
async def test_get_compute_dashboard(mock_task_queue, mock_redis):
    """Test getting complete compute dashboard"""
    dashboard = await get_compute_dashboard()
    
    assert dashboard.overall_metrics.total_jobs == 100
    assert dashboard.overall_metrics.jobs_pending == 10
    assert dashboard.overall_metrics.jobs_running == 5
    assert dashboard.overall_metrics.jobs_completed == 80
    assert dashboard.overall_metrics.jobs_failed == 5
    assert dashboard.overall_metrics.success_rate == 0.94  # 80 / (80 + 5)
    assert dashboard.overall_metrics.failure_rate == 0.06  # 5 / (80 + 5)


@pytest.mark.asyncio
async def test_get_job_execution_metrics(mock_task_queue, mock_redis):
    """Test getting job execution metrics"""
    metrics = await get_job_execution_metrics()
    
    assert len(metrics) == 3  # light, heavy, gpu
    assert all(m.compute_type in ["light_python", "heavy_compute", "gpu_compute"] for m in metrics)


@pytest.mark.asyncio
async def test_get_worker_utilization_metrics(mock_redis):
    """Test getting worker utilization metrics"""
    metrics = await get_worker_utilization_metrics()
    
    assert len(metrics) == 3  # light, heavy, gpu
    assert all(m.worker_type in ["light", "heavy", "gpu"] for m in metrics)


@pytest.mark.asyncio
async def test_get_queue_depth_metrics(mock_redis):
    """Test getting queue depth metrics"""
    metrics = await get_queue_depth_metrics()
    
    assert len(metrics) == 3  # light, heavy, gpu
    assert all(m.compute_type in ["light", "heavy", "gpu"] for m in metrics)


@pytest.mark.asyncio
async def test_alert_triggering_high_failure_rate(mock_task_queue, mock_redis):
    """Test alert triggering for high failure rate"""
    # Mock high failure rate
    mock_task_queue.get_stats.return_value = {
        "total_tasks": 100,
        "pending": 0,
        "running": 0,
        "completed": 90,
        "failed": 10,  # 10% failure rate (> 5% threshold)
        "cancelled": 0,
        "queue_size": 0,
        "max_concurrent": 10,
    }
    
    dashboard = await get_compute_dashboard()
    
    # Should have alert for high failure rate
    assert len(dashboard.active_alerts) > 0
    assert any(a.metric == "compute_job_failure_rate" for a in dashboard.active_alerts)


@pytest.mark.asyncio
async def test_alert_triggering_high_queue_depth(mock_task_queue, mock_redis):
    """Test alert triggering for high queue depth"""
    # Mock high queue depth
    mock_task_queue.get_stats.return_value = {
        "total_tasks": 1500,
        "pending": 1200,  # > 1000 threshold
        "running": 5,
        "completed": 290,
        "failed": 5,
        "cancelled": 0,
        "queue_size": 1200,
        "max_concurrent": 10,
    }
    
    dashboard = await get_compute_dashboard()
    
    # Should have alert for high queue depth
    assert len(dashboard.active_alerts) > 0
    assert any(a.metric == "queue_depth" for a in dashboard.active_alerts)


@pytest.mark.asyncio
async def test_no_alerts_normal_conditions(mock_task_queue, mock_redis):
    """Test no alerts under normal conditions"""
    # Mock normal conditions
    mock_task_queue.get_stats.return_value = {
        "total_tasks": 100,
        "pending": 10,
        "running": 5,
        "completed": 84,  # 2% failure rate (< 5% threshold)
        "failed": 1,
        "cancelled": 0,
        "queue_size": 15,  # < 1000 threshold
        "max_concurrent": 10,
    }
    
    # Mock normal worker utilization
    mock_redis.keys = AsyncMock(return_value=[
        "worker:light:1",
        "worker:light:2",
        "worker:heavy:1",
    ])
    mock_redis.get = AsyncMock(return_value={
        "worker_id": "test",
        "status": "running",
        "max_concurrent": 5,
        "processed_count": 10,
        "failed_count": 0,
    })
    
    dashboard = await get_compute_dashboard()
    
    # Should have no alerts
    assert len(dashboard.active_alerts) == 0
