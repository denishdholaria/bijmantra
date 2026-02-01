"""
CHAITANYA API - Central Orchestrator Endpoints
Part of ASHTA-STAMBHA (Eight Pillars) security framework

The unified control plane for RAKSHAKA (healing) and PRAHARI (defense).

Endpoints:
- GET /chaitanya/posture - Current system posture
- PUT /chaitanya/posture - Set posture manually
- GET /chaitanya/posture/history - Posture change history
- GET /chaitanya/dashboard - Unified dashboard
- POST /chaitanya/event - Handle security event
- POST /chaitanya/anomaly - Handle health anomaly
- GET /chaitanya/actions - Orchestrated actions history
- GET /chaitanya/config - Current configuration
- PUT /chaitanya/config - Update configuration
- PUT /chaitanya/auto-response - Enable/disable auto-response
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.services.chaitanya import chaitanya, PostureLevel

router = APIRouter(prefix="/chaitanya", tags=["CHAITANYA Orchestrator"])


class PostureRequest(BaseModel):
    level: str
    reason: Optional[str] = None


class AutoResponseRequest(BaseModel):
    enabled: bool


class SecurityEventRequest(BaseModel):
    layer: str = "application"
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "low"


class AnomalyRequest(BaseModel):
    id: Optional[str] = None
    type: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None


class ThresholdUpdate(BaseModel):
    thresholds: Dict[str, Dict[str, Any]]


@router.get("/posture")
async def get_posture():
    """
    Get current system posture.
    Assesses health (RAKSHAKA) and security (PRAHARI) to determine overall posture.
    """
    posture = await chaitanya.assess_posture()
    return posture.to_dict()


@router.put("/posture")
async def set_posture(request: PostureRequest):
    """
    Manually set system posture level.
    Use for emergency escalation or de-escalation.
    """
    try:
        level = PostureLevel(request.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid posture level. Valid options: {[p.value for p in PostureLevel]}"
        )
    
    result = chaitanya.set_posture(level, request.reason or "Manual override")
    return result


@router.get("/posture/history")
async def get_posture_history(limit: int = 50):
    """Get history of posture changes."""
    history = chaitanya.get_posture_history(limit)
    return {
        "count": len(history),
        "history": history
    }


@router.get("/dashboard")
async def get_unified_dashboard():
    """
    Get unified dashboard data from all systems.
    Combines RAKSHAKA health, PRAHARI security, and orchestration data.
    """
    return await chaitanya.get_unified_dashboard()


@router.post("/event")
async def handle_security_event(event: SecurityEventRequest):
    """
    Handle a security event through the full CHAITANYA pipeline.
    Coordinates PRAHARI analysis and response, then reassesses posture.
    """
    result = await chaitanya.handle_security_event({
        "layer": event.layer,
        "event_type": event.event_type,
        "source_ip": event.source_ip,
        "user_id": event.user_id,
        "endpoint": event.endpoint,
        "details": event.details or {},
        "severity": event.severity,
    })
    return result


@router.post("/anomaly")
async def handle_health_anomaly(anomaly: AnomalyRequest):
    """
    Handle a health anomaly through the full CHAITANYA pipeline.
    Coordinates RAKSHAKA healing and reassesses posture.
    """
    result = await chaitanya.handle_health_anomaly({
        "id": anomaly.id,
        "type": anomaly.type,
        "metric_name": anomaly.metric_name,
        "current_value": anomaly.current_value,
    })
    return result


@router.get("/actions")
async def get_orchestrated_actions(limit: int = 50):
    """Get history of orchestrated actions across systems."""
    actions = chaitanya.get_orchestrated_actions(limit)
    return {
        "count": len(actions),
        "actions": actions
    }


@router.get("/config")
async def get_config():
    """Get current CHAITANYA configuration."""
    return chaitanya.get_config()


@router.put("/config/thresholds")
async def update_thresholds(request: ThresholdUpdate):
    """
    Update posture escalation thresholds.
    
    Example:
    {
        "thresholds": {
            "elevated": {"threats": 2, "anomalies": 5},
            "high": {"threats": 5, "security_score": 40}
        }
    }
    """
    return chaitanya.update_thresholds(request.thresholds)


@router.put("/auto-response")
async def set_auto_response(request: AutoResponseRequest):
    """Enable or disable automatic response to threats and anomalies."""
    return chaitanya.set_auto_response(request.enabled)


@router.get("/status")
async def get_status():
    """Get quick status summary."""
    posture = await chaitanya.assess_posture()
    config = chaitanya.get_config()
    
    return {
        "posture_level": posture.level.value,
        "overall_score": posture.overall_score,
        "health_score": posture.health_score,
        "security_score": posture.security_score,
        "active_threats": posture.active_threats,
        "active_anomalies": posture.active_anomalies,
        "auto_response_enabled": config["auto_response_enabled"],
        "recommendations_count": len(posture.recommendations),
    }


@router.get("/security-config")
async def get_security_config():
    """
    Get current security configuration.
    Shows all security settings loaded from environment.
    """
    from app.core.security_config import get_security_config
    config = get_security_config()
    
    return {
        "enabled": config.enabled,
        "auto_response_enabled": config.auto_response_enabled,
        "audit_logging_enabled": config.audit_logging_enabled,
        "middleware_enabled": config.middleware_enabled,
        "thresholds": {
            "elevated": {
                "threats": config.thresholds.elevated_threats,
                "anomalies": config.thresholds.elevated_anomalies,
                "security_score": config.thresholds.elevated_security_score,
            },
            "high": {
                "threats": config.thresholds.high_threats,
                "anomalies": config.thresholds.high_anomalies,
                "security_score": config.thresholds.high_security_score,
            },
            "severe": {
                "threats": config.thresholds.severe_threats,
                "anomalies": config.thresholds.severe_anomalies,
                "security_score": config.thresholds.severe_security_score,
            },
            "lockdown": {
                "threats": config.thresholds.lockdown_threats,
                "anomalies": config.thresholds.lockdown_anomalies,
                "security_score": config.thresholds.lockdown_security_score,
            },
        },
        "rate_limits": {
            "default": {"limit": config.rate_limits.default_limit, "window": config.rate_limits.default_window},
            "auth": {"limit": config.rate_limits.auth_limit, "window": config.rate_limits.auth_window},
            "api": {"limit": config.rate_limits.api_limit, "window": config.rate_limits.api_window},
        },
        "blocking": {
            "default_duration": config.default_block_duration,
            "max_duration": config.max_block_duration,
        },
        "anomaly_detection": {
            "baseline_window": config.anomaly_baseline_window,
            "api_latency_warn": config.api_latency_warn,
            "api_latency_crit": config.api_latency_crit,
            "error_rate_warn": config.error_rate_warn,
            "error_rate_crit": config.error_rate_crit,
        },
        "audit": {
            "retention_days": config.audit_retention_days,
            "max_memory_entries": config.audit_max_memory_entries,
        },
        "redis_configured": config.redis_url is not None,
        "security_headers_enabled": config.enable_security_headers,
    }


@router.get("/storage-stats")
async def get_storage_stats():
    """Get security storage statistics (Redis or in-memory)."""
    from app.services.redis_security import redis_security
    return await redis_security.get_stats()
