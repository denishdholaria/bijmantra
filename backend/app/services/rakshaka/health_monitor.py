"""
RAKSHAKA Health Monitor - System health metrics collection
Pillar 1: DRISHTI (दृष्टि) - Vision/Sight - All-seeing observation
"""

import time
import psutil
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    latency_ms: float
    error_rate: float
    last_check: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """
    System health monitoring service.
    Collects metrics from API, database, memory, CPU, and tracks error rates.
    """

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self._api_latencies: deque = deque(maxlen=history_size)
        self._db_latencies: deque = deque(maxlen=history_size)
        self._error_counts: deque = deque(maxlen=history_size)
        self._request_counts: deque = deque(maxlen=history_size)
        self._components: Dict[str, ComponentHealth] = {}
        self._start_time = datetime.now(UTC)

    def record_api_latency(self, endpoint: str, latency_ms: float):
        """Record API response time"""
        self._api_latencies.append(MetricPoint(
            timestamp=datetime.now(UTC),
            value=latency_ms,
            tags={"endpoint": endpoint}
        ))

    def record_db_latency(self, query_type: str, latency_ms: float):
        """Record database query time"""
        self._db_latencies.append(MetricPoint(
            timestamp=datetime.now(UTC),
            value=latency_ms,
            tags={"query_type": query_type}
        ))

    def record_error(self, error_type: str, endpoint: str = ""):
        """Record an error occurrence"""
        self._error_counts.append(MetricPoint(
            timestamp=datetime.now(UTC),
            value=1,
            tags={"error_type": error_type, "endpoint": endpoint}
        ))

    def record_request(self, endpoint: str):
        """Record a request"""
        self._request_counts.append(MetricPoint(
            timestamp=datetime.now(UTC),
            value=1,
            tags={"endpoint": endpoint}
        ))

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "status": self._get_status_from_percent(cpu_percent, 70, 90)
            },
            "memory": {
                "percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "status": self._get_status_from_percent(memory.percent, 70, 90)
            },
            "disk": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "status": self._get_status_from_percent(disk.percent, 80, 95)
            }
        }

    def _get_status_from_percent(self, value: float, warn: float, crit: float) -> str:
        if value >= crit:
            return HealthStatus.CRITICAL.value
        elif value >= warn:
            return HealthStatus.DEGRADED.value
        return HealthStatus.HEALTHY.value

    def _calculate_avg(self, metrics: deque, minutes: int = 5) -> float:
        """Calculate average of metrics in the last N minutes"""
        cutoff = datetime.now(UTC) - timedelta(minutes=minutes)
        recent = [m.value for m in metrics if m.timestamp > cutoff]
        return round(sum(recent) / len(recent), 2) if recent else 0.0

    def _count_recent(self, metrics: deque, minutes: int = 5) -> int:
        """Count metrics in the last N minutes"""
        cutoff = datetime.now(UTC) - timedelta(minutes=minutes)
        return sum(1 for m in metrics if m.timestamp > cutoff)

    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        avg_latency = self._calculate_avg(self._api_latencies)
        request_count = self._count_recent(self._request_counts)
        error_count = self._count_recent(self._error_counts)
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0

        return {
            "avg_latency_ms": avg_latency,
            "requests_5min": request_count,
            "errors_5min": error_count,
            "error_rate_percent": round(error_rate, 2),
            "latency_status": self._get_latency_status(avg_latency),
            "error_status": self._get_error_status(error_rate)
        }

    def _get_latency_status(self, latency_ms: float) -> str:
        if latency_ms > 1000:
            return HealthStatus.CRITICAL.value
        elif latency_ms > 500:
            return HealthStatus.DEGRADED.value
        return HealthStatus.HEALTHY.value

    def _get_error_status(self, error_rate: float) -> str:
        if error_rate > 5:
            return HealthStatus.CRITICAL.value
        elif error_rate > 1:
            return HealthStatus.DEGRADED.value
        return HealthStatus.HEALTHY.value

    def get_db_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        avg_latency = self._calculate_avg(self._db_latencies)
        return {
            "avg_latency_ms": avg_latency,
            "queries_5min": self._count_recent(self._db_latencies),
            "status": self._get_latency_status(avg_latency * 2)  # DB can be slower
        }

    def register_component(self, name: str, status: HealthStatus,
                          latency_ms: float = 0, error_rate: float = 0,
                          details: Dict[str, Any] = None):
        """Register or update a component's health status"""
        self._components[name] = ComponentHealth(
            name=name,
            status=status,
            latency_ms=latency_ms,
            error_rate=error_rate,
            last_check=datetime.now(UTC),
            details=details or {}
        )

    def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        """Get health status of a specific component"""
        return self._components.get(name)

    def get_all_components(self) -> List[Dict[str, Any]]:
        """Get health status of all registered components"""
        return [
            {
                "name": c.name,
                "status": c.status.value,
                "latency_ms": c.latency_ms,
                "error_rate": c.error_rate,
                "last_check": c.last_check.isoformat(),
                "details": c.details
            }
            for c in self._components.values()
        ]

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        system = self.get_system_metrics()
        api = self.get_api_metrics()
        db = self.get_db_metrics()
        components = self.get_all_components()

        # Determine overall status
        statuses = [
            system["cpu"]["status"],
            system["memory"]["status"],
            api["latency_status"],
            api["error_status"],
            db["status"]
        ]
        statuses.extend([c["status"] for c in components])

        if HealthStatus.CRITICAL.value in statuses:
            overall = HealthStatus.CRITICAL
        elif HealthStatus.DEGRADED.value in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        uptime = datetime.now(UTC) - self._start_time

        return {
            "status": overall.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],
            "system": system,
            "api": api,
            "database": db,
            "components": components,
            "summary": {
                "healthy_components": sum(1 for s in statuses if s == HealthStatus.HEALTHY.value),
                "degraded_components": sum(1 for s in statuses if s == HealthStatus.DEGRADED.value),
                "critical_components": sum(1 for s in statuses if s == HealthStatus.CRITICAL.value),
            }
        }

    def get_metrics_history(self, metric_type: str, minutes: int = 60) -> List[Dict]:
        """Get historical metrics for charting"""
        cutoff = datetime.now(UTC) - timedelta(minutes=minutes)

        if metric_type == "api_latency":
            data = self._api_latencies
        elif metric_type == "db_latency":
            data = self._db_latencies
        elif metric_type == "errors":
            data = self._error_counts
        elif metric_type == "requests":
            data = self._request_counts
        else:
            return []

        return [
            {"timestamp": m.timestamp.isoformat(), "value": m.value, "tags": m.tags}
            for m in data if m.timestamp > cutoff
        ]


# Singleton instance
health_monitor = HealthMonitor()
