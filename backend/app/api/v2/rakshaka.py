"""
RAKSHAKA API - Self-Healing System Endpoints
Part of ASHTA-STAMBHA (Eight Pillars) security framework

Endpoints:
- GET /rakshaka/health - Current health status
- GET /rakshaka/metrics - All metrics
- GET /rakshaka/anomalies - Detected anomalies
- GET /rakshaka/incidents - Incident/healing history
- POST /rakshaka/heal - Trigger manual healing
- GET /rakshaka/strategies - Available strategies
- GET /rakshaka/config - Current configuration
- PUT /rakshaka/config - Update configuration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.services.rakshaka import health_monitor, anomaly_detector, healer
from app.api.deps import get_current_user

router = APIRouter(prefix="/rakshaka", tags=["RAKSHAKA Self-Healing"], dependencies=[Depends(get_current_user)])


class HealRequest(BaseModel):
    strategy: str
    anomaly_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class ConfigUpdate(BaseModel):
    thresholds: Optional[Dict[str, Dict[str, float]]] = None
    baseline_window: Optional[int] = None


@router.get("/health")
async def get_health():
    """
    Get current system health status.
    Returns overall health, system metrics, API metrics, and component status.
    """
    return health_monitor.get_overall_health()


@router.get("/metrics")
async def get_metrics(metric_type: str = "all", minutes: int = 60):
    """
    Get system metrics.
    
    Args:
        metric_type: Type of metrics (all, api_latency, db_latency, errors, requests)
        minutes: Time window in minutes
    """
    if metric_type == "all":
        return {
            "system": health_monitor.get_system_metrics(),
            "api": health_monitor.get_api_metrics(),
            "database": health_monitor.get_db_metrics(),
            "components": health_monitor.get_all_components(),
            "baselines": anomaly_detector.get_config()["baselines"]
        }
    
    history = health_monitor.get_metrics_history(metric_type, minutes)
    return {
        "metric_type": metric_type,
        "minutes": minutes,
        "data_points": len(history),
        "history": history
    }


@router.get("/anomalies")
async def get_anomalies(active_only: bool = True, limit: int = 100):
    """
    Get detected anomalies.
    
    Args:
        active_only: If True, return only unresolved anomalies
        limit: Maximum number of anomalies to return
    """
    if active_only:
        anomalies = anomaly_detector.get_active_anomalies()
    else:
        anomalies = anomaly_detector.get_all_anomalies(limit)
    
    return {
        "count": len(anomalies),
        "active_only": active_only,
        "anomalies": anomalies
    }


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(anomaly_id: str):
    """Mark an anomaly as resolved"""
    success = anomaly_detector.resolve_anomaly(anomaly_id)
    if not success:
        raise HTTPException(status_code=404, detail="Anomaly not found or already resolved")
    return {"message": f"Anomaly {anomaly_id} resolved", "success": True}


@router.get("/incidents")
async def get_incidents(limit: int = 50):
    """
    Get healing incident history.
    Shows all healing actions taken by the system.
    """
    history = healer.get_healing_history(limit)
    stats = healer.get_stats()
    
    return {
        "count": len(history),
        "stats": stats,
        "incidents": history
    }


@router.post("/heal")
async def trigger_healing(request: HealRequest):
    """
    Trigger a manual healing action.
    
    Args:
        strategy: Healing strategy to execute
        anomaly_id: Optional anomaly ID this healing addresses
        params: Optional parameters for the strategy
    """
    from app.services.rakshaka.healer import HealingStrategy
    
    try:
        strategy = HealingStrategy(request.strategy)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid strategy. Valid options: {[s.value for s in HealingStrategy]}"
        )
    
    action = await healer.heal(strategy, request.anomaly_id, request.params)
    
    return {
        "message": f"Healing action {action.id} executed",
        "action": healer._action_to_dict(action)
    }


@router.get("/strategies")
async def get_strategies():
    """
    Get available healing strategies.
    Returns list of strategies with descriptions.
    """
    return {
        "strategies": healer.get_available_strategies(),
        "recommendations": {
            "latency_spike": ["clear_cache", "reset_connections"],
            "error_rate": ["circuit_break", "rate_limit"],
            "memory_pressure": ["garbage_collect", "clear_cache"],
            "cpu_spike": ["rate_limit"],
            "connection_pool": ["reset_connections"]
        }
    }


@router.get("/config")
async def get_config():
    """
    Get current RAKSHAKA configuration.
    Includes anomaly detection thresholds and baseline settings.
    """
    return {
        "anomaly_detection": anomaly_detector.get_config(),
        "healing": {
            "available_strategies": [s.value for s in healer._strategies.keys()],
            "stats": healer.get_stats()
        }
    }


@router.put("/config")
async def update_config(config: ConfigUpdate):
    """
    Update RAKSHAKA configuration.
    
    Args:
        thresholds: Anomaly detection thresholds
        baseline_window: Number of data points for baseline calculation
    """
    updated = anomaly_detector.update_config(
        thresholds=config.thresholds,
        baseline_window=config.baseline_window
    )
    return {
        "message": "Configuration updated",
        "config": updated
    }


# Demo endpoint to simulate metrics (for testing)
@router.post("/simulate")
async def simulate_metrics(
    api_latency: float = 100,
    db_latency: float = 50,
    error_rate: float = 0.5
):
    """
    Simulate metrics for testing anomaly detection.
    This endpoint is for development/testing only.
    """
    # Record simulated metrics
    health_monitor.record_api_latency("/test", api_latency)
    health_monitor.record_db_latency("SELECT", db_latency)
    health_monitor.record_request("/test")
    
    if error_rate > 0:
        import random
        if random.random() < error_rate / 100:
            health_monitor.record_error("simulated", "/test")
    
    # Check for anomalies
    anomalies = []
    api_anomaly = anomaly_detector.check_anomaly("api_latency_ms", api_latency)
    if api_anomaly:
        anomalies.append(anomaly_detector._anomaly_to_dict(api_anomaly))
    
    db_anomaly = anomaly_detector.check_anomaly("db_latency_ms", db_latency)
    if db_anomaly:
        anomalies.append(anomaly_detector._anomaly_to_dict(db_anomaly))
    
    return {
        "message": "Metrics simulated",
        "input": {"api_latency": api_latency, "db_latency": db_latency, "error_rate": error_rate},
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies
    }
