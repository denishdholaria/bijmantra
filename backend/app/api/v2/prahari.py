"""
PRAHARI API - Defense & Monitoring System Endpoints
Part of ASHTA-STAMBHA (Eight Pillars) security framework

Endpoints:
- GET /prahari/events - Recent security events
- GET /prahari/events/stats - Event statistics
- GET /prahari/threats - Threat assessments
- GET /prahari/threats/{id} - Specific threat assessment
- POST /prahari/analyze - Analyze a security event
- GET /prahari/blocked - Blocked IPs and users
- POST /prahari/block - Block IP or user
- DELETE /prahari/block/{type}/{target} - Unblock
- GET /prahari/reputation/{ip} - IP reputation
- POST /prahari/reputation/bad - Add to bad IP list
- POST /prahari/reputation/good - Add to good IP list
- GET /prahari/responses - Response history
- GET /prahari/stats - Overall statistics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.api.deps import get_current_user
from app.services.prahari import (
    security_observer, threat_analyzer, threat_responder,
    SecurityEvent, EventSeverity, ObservationLayer,
    ThreatCategory, ThreatConfidence, ResponseAction
)

router = APIRouter(prefix="/prahari", tags=["PRAHARI Defense"], dependencies=[Depends(get_current_user)])


class SecurityEventInput(BaseModel):
    layer: str = "application"
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "low"


class BlockRequest(BaseModel):
    target_type: str  # "ip" or "user"
    target: str
    duration_seconds: int = 3600
    reason: Optional[str] = None


class IPReputationRequest(BaseModel):
    ip: str


@router.get("/events")
async def get_security_events(
    limit: int = 100,
    layer: Optional[str] = None,
    min_severity: Optional[str] = None
):
    """Get recent security events observed by DRISHTI."""
    layer_enum = ObservationLayer(layer) if layer else None
    severity_enum = EventSeverity(min_severity) if min_severity else None
    
    events = security_observer.get_recent_events(
        limit=limit,
        layer=layer_enum,
        min_severity=severity_enum
    )
    
    return {
        "count": len(events),
        "events": events
    }


@router.get("/events/stats")
async def get_event_stats():
    """Get security event statistics."""
    return security_observer.get_stats()


@router.get("/events/suspicious-ips")
async def get_suspicious_ips():
    """Get IPs with suspicious activity."""
    return {
        "suspicious_ips": security_observer.get_suspicious_ips()
    }


@router.get("/threats")
async def get_threat_assessments(
    limit: int = 100,
    min_confidence: Optional[str] = None
):
    """Get threat assessments from VIVEK analyzer."""
    confidence_enum = ThreatConfidence(min_confidence) if min_confidence else None
    
    assessments = threat_analyzer.get_recent_assessments(
        limit=limit,
        min_confidence=confidence_enum
    )
    
    return {
        "count": len(assessments),
        "assessments": assessments
    }


@router.get("/threats/stats")
async def get_threat_stats():
    """Get threat analysis statistics."""
    return threat_analyzer.get_stats()


@router.post("/analyze")
async def analyze_event(event: SecurityEventInput):
    """
    Analyze a security event and get threat assessment.
    This triggers the full PRAHARI pipeline: observe -> analyze -> respond.
    """
    # Create and observe the event
    observed = await security_observer.observe_request(
        endpoint=event.endpoint or "/unknown",
        method="POST",
        source_ip=event.source_ip or "unknown",
        user_id=event.user_id,
        status_code=200,
    )
    
    if not observed:
        # Create a minimal event for analysis
        observed = SecurityEvent(
            id=security_observer._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            layer=ObservationLayer(event.layer),
            event_type=event.event_type,
            source_ip=event.source_ip,
            user_id=event.user_id,
            endpoint=event.endpoint,
            details=event.details or {},
            severity=EventSeverity(event.severity),
        )
    
    # Analyze the threat
    assessment = await threat_analyzer.analyze(observed)
    
    # Auto-respond if high confidence
    responses = []
    if assessment.confidence_score >= 60:
        responses = await threat_responder.respond(assessment)
    
    return {
        "event": observed.to_dict(),
        "assessment": assessment.to_dict(),
        "responses": [r.to_dict() for r in responses],
    }


@router.get("/blocked")
async def get_blocked():
    """Get currently blocked IPs and users."""
    return {
        "blocked_ips": threat_responder.get_blocked_ips(),
        "blocked_users": threat_responder.get_blocked_users(),
    }


@router.post("/block")
async def block_target(request: BlockRequest):
    """Manually block an IP or user."""
    from app.services.prahari.responder import ResponseAction
    
    if request.target_type == "ip":
        # Create a dummy assessment for the block action
        from app.services.prahari.threat_analyzer import ThreatAssessment, ThreatCategory
        assessment = ThreatAssessment(
            id="MANUAL",
            event_id="MANUAL",
            timestamp=datetime.now(timezone.utc),
            category=ThreatCategory.UNKNOWN,
            confidence=ThreatConfidence.CONFIRMED,
            confidence_score=100,
            severity=EventSeverity.HIGH,
            context={"source_ip": request.target},
        )
        responses = await threat_responder.respond(
            assessment,
            actions=[ResponseAction.BLOCK_IP],
            params={"target": request.target, "duration_seconds": request.duration_seconds}
        )
    elif request.target_type == "user":
        from app.services.prahari.threat_analyzer import ThreatAssessment, ThreatCategory
        assessment = ThreatAssessment(
            id="MANUAL",
            event_id="MANUAL",
            timestamp=datetime.now(timezone.utc),
            category=ThreatCategory.UNKNOWN,
            confidence=ThreatConfidence.CONFIRMED,
            confidence_score=100,
            severity=EventSeverity.HIGH,
            context={"user_id": request.target},
        )
        responses = await threat_responder.respond(
            assessment,
            actions=[ResponseAction.BLOCK_USER],
            params={"target": request.target, "duration_seconds": request.duration_seconds}
        )
    else:
        raise HTTPException(status_code=400, detail="target_type must be 'ip' or 'user'")
    
    return {
        "message": f"{request.target_type} {request.target} blocked",
        "responses": [r.to_dict() for r in responses],
    }


@router.delete("/block/ip/{ip}")
async def unblock_ip(ip: str):
    """Unblock an IP address."""
    success = threat_responder.unblock_ip(ip)
    if not success:
        raise HTTPException(status_code=404, detail="IP not found in block list")
    return {"message": f"IP {ip} unblocked", "success": True}


@router.delete("/block/user/{user_id}")
async def unblock_user(user_id: str):
    """Unblock a user."""
    success = threat_responder.unblock_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in block list")
    return {"message": f"User {user_id} unblocked", "success": True}


@router.get("/reputation/{ip}")
async def get_ip_reputation(ip: str):
    """Get reputation information for an IP address."""
    return threat_analyzer.get_ip_reputation(ip)


@router.post("/reputation/bad")
async def add_bad_ip(request: IPReputationRequest):
    """Add an IP to the known bad list."""
    threat_analyzer.add_known_bad_ip(request.ip)
    return {"message": f"IP {request.ip} added to known bad list"}


@router.post("/reputation/good")
async def add_good_ip(request: IPReputationRequest):
    """Add an IP to the known good list (whitelist)."""
    threat_analyzer.add_known_good_ip(request.ip)
    return {"message": f"IP {request.ip} added to known good list"}


@router.get("/responses")
async def get_response_history(limit: int = 100):
    """Get history of response actions taken by SHAKTI."""
    return {
        "count": len(threat_responder.get_response_history(limit)),
        "responses": threat_responder.get_response_history(limit),
    }


@router.get("/responses/stats")
async def get_response_stats():
    """Get response action statistics."""
    return threat_responder.get_stats()


@router.get("/stats")
async def get_prahari_stats():
    """Get overall PRAHARI statistics."""
    return {
        "observer": security_observer.get_stats(),
        "analyzer": threat_analyzer.get_stats(),
        "responder": threat_responder.get_stats(),
    }


@router.get("/check/ip/{ip}")
async def check_ip_status(ip: str):
    """Check if an IP is blocked or rate-limited."""
    return {
        "ip": ip,
        "blocked": threat_responder.is_ip_blocked(ip),
        "rate_limited": threat_responder.get_rate_limit(ip) is not None,
        "rate_limit": threat_responder.get_rate_limit(ip),
        "honeypot_target": threat_responder.is_honeypot_target(ip),
        "reputation": threat_analyzer.get_ip_reputation(ip),
    }


@router.get("/check/user/{user_id}")
async def check_user_status(user_id: str):
    """Check if a user is blocked."""
    return {
        "user_id": user_id,
        "blocked": threat_responder.is_user_blocked(user_id),
    }
