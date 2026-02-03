"""
CHAITANYA (चैतन्य) - The Orchestrator / Consciousness

Central coordination between RAKSHAKA (healing) and PRAHARI (defense).
Provides unified system awareness and adaptive response.
"""

import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PostureLevel(str, Enum):
    """System security posture levels."""
    NORMAL = "normal"  # Business as usual
    ELEVATED = "elevated"  # Increased monitoring
    HIGH = "high"  # Active threats detected
    SEVERE = "severe"  # Under attack, maximum defense
    LOCKDOWN = "lockdown"  # Emergency mode, minimal operations


@dataclass
class SystemPosture:
    """Current system security and health posture."""
    level: PostureLevel
    health_score: float  # 0-100
    security_score: float  # 0-100
    overall_score: float  # 0-100
    active_threats: int
    active_anomalies: int
    blocked_ips: int
    last_incident: Optional[datetime]
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "level": self.level.value,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "overall_score": self.overall_score,
            "active_threats": self.active_threats,
            "active_anomalies": self.active_anomalies,
            "blocked_ips": self.blocked_ips,
            "last_incident": self.last_incident.isoformat() if self.last_incident else None,
            "recommendations": self.recommendations,
        }


@dataclass
class OrchestratedAction:
    """Record of an orchestrated action across systems."""
    id: str
    timestamp: datetime
    trigger: str  # What triggered this action
    systems_involved: List[str]  # rakshaka, prahari, etc.
    actions_taken: List[Dict[str, Any]]
    posture_before: PostureLevel
    posture_after: PostureLevel
    success: bool
    notes: str = ""


class Chaitanya:
    """
    CHAITANYA - Central Orchestration Engine.
    
    Coordinates RAKSHAKA (self-healing) and PRAHARI (defense) systems.
    Maintains unified awareness of system health and security.
    """
    
    def __init__(self):
        self._current_posture = PostureLevel.NORMAL
        self._posture_history: List[Dict] = []
        self._orchestrated_actions: List[OrchestratedAction] = []
        self._action_counter = 0
        self._last_assessment: Optional[datetime] = None
        self._auto_response_enabled = True
        
        # Posture escalation thresholds
        self._thresholds = {
            "elevated": {"threats": 1, "anomalies": 3, "security_score": 70},
            "high": {"threats": 3, "anomalies": 5, "security_score": 50},
            "severe": {"threats": 5, "anomalies": 10, "security_score": 30},
            "lockdown": {"threats": 10, "anomalies": 20, "security_score": 10},
        }
    
    def _generate_action_id(self) -> str:
        self._action_counter += 1
        return f"ORC-{datetime.now(UTC).strftime('%Y%m%d')}-{self._action_counter:06d}"
    
    async def assess_posture(self) -> SystemPosture:
        """Assess current system posture by querying RAKSHAKA and PRAHARI."""
        
        # Import here to avoid circular imports
        from app.services.rakshaka import health_monitor, anomaly_detector
        from app.services.prahari import security_observer, threat_analyzer, threat_responder
        
        # Get health metrics from RAKSHAKA
        health = health_monitor.get_overall_health()
        anomalies = anomaly_detector.get_active_anomalies()
        
        # Get security metrics from PRAHARI
        security_stats = security_observer.get_stats()
        threat_stats = threat_analyzer.get_stats()
        response_stats = threat_responder.get_stats()
        
        # Calculate scores
        health_score = self._calculate_health_score(health)
        security_score = self._calculate_security_score(security_stats, threat_stats)
        overall_score = (health_score * 0.4 + security_score * 0.6)
        
        # Count active issues
        active_threats = threat_stats.get("assessments_24h", 0)
        active_anomalies = len(anomalies)
        blocked_ips = response_stats.get("blocked_ips", 0)
        
        # Determine posture level
        posture_level = self._determine_posture_level(
            active_threats, active_anomalies, security_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            health, security_stats, threat_stats, posture_level
        )
        
        # Find last incident
        recent_events = security_observer.get_recent_events(limit=1)
        last_incident = None
        if recent_events:
            last_incident = datetime.fromisoformat(recent_events[0]["timestamp"])
        
        posture = SystemPosture(
            level=posture_level,
            health_score=round(health_score, 1),
            security_score=round(security_score, 1),
            overall_score=round(overall_score, 1),
            active_threats=active_threats,
            active_anomalies=active_anomalies,
            blocked_ips=blocked_ips,
            last_incident=last_incident,
            recommendations=recommendations,
        )
        
        # Update posture if changed
        if posture_level != self._current_posture:
            await self._handle_posture_change(self._current_posture, posture_level)
            self._current_posture = posture_level
        
        self._last_assessment = datetime.now(UTC)
        return posture
    
    def _calculate_health_score(self, health: Dict) -> float:
        """Calculate health score from RAKSHAKA metrics."""
        score = 100.0
        
        # CPU impact
        cpu = health.get("system", {}).get("cpu", {}).get("percent", 0)
        if cpu > 90:
            score -= 30
        elif cpu > 70:
            score -= 15
        
        # Memory impact
        mem = health.get("system", {}).get("memory", {}).get("percent", 0)
        if mem > 90:
            score -= 30
        elif mem > 70:
            score -= 15
        
        # API latency impact
        latency = health.get("api", {}).get("avg_latency_ms", 0)
        if latency > 1000:
            score -= 20
        elif latency > 500:
            score -= 10
        
        # Error rate impact
        error_rate = health.get("api", {}).get("error_rate_percent", 0)
        if error_rate > 5:
            score -= 25
        elif error_rate > 1:
            score -= 10
        
        return max(0, score)

    def _calculate_security_score(self, security_stats: Dict, threat_stats: Dict) -> float:
        """Calculate security score from PRAHARI metrics."""
        score = 100.0
        
        # Events in last hour
        events_hour = security_stats.get("events_last_hour", 0)
        if events_hour > 50:
            score -= 30
        elif events_hour > 20:
            score -= 15
        elif events_hour > 10:
            score -= 5
        
        # Severity distribution
        by_severity = security_stats.get("by_severity", {})
        score -= by_severity.get("critical", 0) * 15
        score -= by_severity.get("high", 0) * 8
        score -= by_severity.get("medium", 0) * 3
        
        # Threat assessments
        threats_24h = threat_stats.get("assessments_24h", 0)
        if threats_24h > 20:
            score -= 25
        elif threats_24h > 10:
            score -= 15
        elif threats_24h > 5:
            score -= 5
        
        return max(0, score)
    
    def _determine_posture_level(self, threats: int, anomalies: int, 
                                 security_score: float) -> PostureLevel:
        """Determine appropriate posture level based on metrics."""
        
        if (threats >= self._thresholds["lockdown"]["threats"] or
            security_score <= self._thresholds["lockdown"]["security_score"]):
            return PostureLevel.LOCKDOWN
        
        if (threats >= self._thresholds["severe"]["threats"] or
            anomalies >= self._thresholds["severe"]["anomalies"] or
            security_score <= self._thresholds["severe"]["security_score"]):
            return PostureLevel.SEVERE
        
        if (threats >= self._thresholds["high"]["threats"] or
            anomalies >= self._thresholds["high"]["anomalies"] or
            security_score <= self._thresholds["high"]["security_score"]):
            return PostureLevel.HIGH
        
        if (threats >= self._thresholds["elevated"]["threats"] or
            anomalies >= self._thresholds["elevated"]["anomalies"] or
            security_score <= self._thresholds["elevated"]["security_score"]):
            return PostureLevel.ELEVATED
        
        return PostureLevel.NORMAL
    
    def _generate_recommendations(self, health: Dict, security_stats: Dict,
                                  threat_stats: Dict, posture: PostureLevel) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Health-based recommendations
        if health.get("system", {}).get("cpu", {}).get("percent", 0) > 80:
            recommendations.append("Consider scaling compute resources - CPU usage high")
        
        if health.get("system", {}).get("memory", {}).get("percent", 0) > 80:
            recommendations.append("Memory pressure detected - review memory usage")
        
        if health.get("api", {}).get("error_rate_percent", 0) > 2:
            recommendations.append("Elevated error rate - investigate failing endpoints")
        
        # Security-based recommendations
        if security_stats.get("suspicious_ips_count", 0) > 5:
            recommendations.append("Multiple suspicious IPs detected - review and block if needed")
        
        by_severity = security_stats.get("by_severity", {})
        if by_severity.get("critical", 0) > 0:
            recommendations.append("CRITICAL security events detected - immediate review required")
        
        # Posture-based recommendations
        if posture == PostureLevel.ELEVATED:
            recommendations.append("Elevated posture - increase monitoring frequency")
        elif posture == PostureLevel.HIGH:
            recommendations.append("High alert - consider enabling additional security controls")
        elif posture == PostureLevel.SEVERE:
            recommendations.append("Severe threat level - activate incident response team")
        elif posture == PostureLevel.LOCKDOWN:
            recommendations.append("LOCKDOWN - restrict access to essential operations only")
        
        return recommendations[:5]  # Limit to top 5
    
    async def _handle_posture_change(self, old: PostureLevel, new: PostureLevel):
        """Handle posture level change with appropriate actions."""
        
        logger.warning(f"Posture change: {old.value} -> {new.value}")
        
        self._posture_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "from": old.value,
            "to": new.value,
        })
        
        # Auto-response based on posture escalation
        if not self._auto_response_enabled:
            return
        
        actions_taken = []
        
        if new in [PostureLevel.SEVERE, PostureLevel.LOCKDOWN]:
            # Trigger RAKSHAKA healing
            from app.services.rakshaka import healer
            from app.services.rakshaka.healer import HealingStrategy
            
            action = await healer.heal(HealingStrategy.RATE_LIMIT, params={
                "duration_seconds": 300,
                "requests_per_second": 5,
            })
            actions_taken.append({"system": "rakshaka", "action": "rate_limit", "result": action.result})
        
        if new == PostureLevel.LOCKDOWN:
            # Additional lockdown measures
            logger.critical("LOCKDOWN MODE ACTIVATED")
            actions_taken.append({"system": "chaitanya", "action": "lockdown_alert", "result": "Alert sent"})
        
        # Record orchestrated action
        if actions_taken:
            self._orchestrated_actions.append(OrchestratedAction(
                id=self._generate_action_id(),
                timestamp=datetime.now(UTC),
                trigger=f"posture_change_{old.value}_to_{new.value}",
                systems_involved=list(set(a["system"] for a in actions_taken)),
                actions_taken=actions_taken,
                posture_before=old,
                posture_after=new,
                success=True,
            ))

    async def handle_security_event(self, event_data: Dict) -> Dict[str, Any]:
        """
        Handle a security event by coordinating PRAHARI analysis and response.
        This is the main entry point for security event processing.
        """
        from app.services.prahari import (
            security_observer, threat_analyzer, threat_responder,
            SecurityEvent, ObservationLayer, EventSeverity
        )
        
        # Create security event
        event = SecurityEvent(
            id=event_data.get("id", security_observer._generate_event_id()),
            timestamp=datetime.now(UTC),
            layer=ObservationLayer(event_data.get("layer", "application")),
            event_type=event_data.get("event_type", "unknown"),
            source_ip=event_data.get("source_ip"),
            user_id=event_data.get("user_id"),
            endpoint=event_data.get("endpoint"),
            details=event_data.get("details", {}),
            severity=EventSeverity(event_data.get("severity", "low")),
        )
        
        # Analyze threat
        assessment = await threat_analyzer.analyze(event)
        
        # Auto-respond if enabled and threat is significant
        responses = []
        if self._auto_response_enabled and assessment.confidence_score >= 50:
            responses = await threat_responder.respond(assessment)
        
        # Re-assess posture
        posture = await self.assess_posture()
        
        return {
            "event_id": event.id,
            "assessment": assessment.to_dict(),
            "responses": [r.to_dict() for r in responses],
            "current_posture": posture.to_dict(),
        }
    
    async def handle_health_anomaly(self, anomaly_data: Dict) -> Dict[str, Any]:
        """
        Handle a health anomaly by coordinating RAKSHAKA healing.
        """
        from app.services.rakshaka import anomaly_detector, healer
        from app.services.rakshaka.healer import HealingStrategy
        
        anomaly_type = anomaly_data.get("type", "unknown")
        
        # Get recommended healing strategies
        strategies = healer.recommend_strategies(anomaly_type)
        
        # Execute healing if auto-response enabled
        healing_results = []
        if self._auto_response_enabled and strategies:
            for strategy in strategies[:2]:  # Limit to 2 strategies
                action = await healer.heal(strategy, anomaly_data.get("id"))
                healing_results.append(healer._action_to_dict(action))
        
        # Re-assess posture
        posture = await self.assess_posture()
        
        return {
            "anomaly_type": anomaly_type,
            "recommended_strategies": [s.value for s in strategies],
            "healing_actions": healing_results,
            "current_posture": posture.to_dict(),
        }
    
    def set_posture(self, level: PostureLevel, reason: str = "") -> Dict[str, Any]:
        """Manually set system posture level."""
        old = self._current_posture
        self._current_posture = level
        
        self._posture_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "from": old.value,
            "to": level.value,
            "manual": True,
            "reason": reason,
        })
        
        logger.warning(f"Manual posture change: {old.value} -> {level.value}. Reason: {reason}")
        
        return {
            "previous": old.value,
            "current": level.value,
            "reason": reason,
        }
    
    def set_auto_response(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable automatic response."""
        old = self._auto_response_enabled
        self._auto_response_enabled = enabled
        return {
            "auto_response_enabled": enabled,
            "previous": old,
        }
    
    def get_posture_history(self, limit: int = 50) -> List[Dict]:
        """Get posture change history."""
        return self._posture_history[-limit:]
    
    def get_orchestrated_actions(self, limit: int = 50) -> List[Dict]:
        """Get history of orchestrated actions."""
        return [
            {
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "trigger": a.trigger,
                "systems_involved": a.systems_involved,
                "actions_taken": a.actions_taken,
                "posture_before": a.posture_before.value,
                "posture_after": a.posture_after.value,
                "success": a.success,
                "notes": a.notes,
            }
            for a in self._orchestrated_actions[-limit:]
        ]
    
    def get_config(self) -> Dict[str, Any]:
        """Get current orchestrator configuration."""
        return {
            "auto_response_enabled": self._auto_response_enabled,
            "current_posture": self._current_posture.value,
            "thresholds": self._thresholds,
            "last_assessment": self._last_assessment.isoformat() if self._last_assessment else None,
        }
    
    def update_thresholds(self, thresholds: Dict[str, Dict]) -> Dict[str, Any]:
        """Update posture escalation thresholds."""
        for level, values in thresholds.items():
            if level in self._thresholds:
                self._thresholds[level].update(values)
        return {"thresholds": self._thresholds}
    
    async def get_unified_dashboard(self) -> Dict[str, Any]:
        """Get unified dashboard data from all systems."""
        from app.services.rakshaka import health_monitor, anomaly_detector, healer
        from app.services.prahari import security_observer, threat_analyzer, threat_responder
        
        posture = await self.assess_posture()
        
        return {
            "posture": posture.to_dict(),
            "health": {
                "overall": health_monitor.get_overall_health(),
                "anomalies": anomaly_detector.get_active_anomalies()[:5],
                "healing_stats": healer.get_stats(),
            },
            "security": {
                "events": security_observer.get_recent_events(limit=10),
                "threat_stats": threat_analyzer.get_stats(),
                "response_stats": threat_responder.get_stats(),
                "blocked_ips": threat_responder.get_blocked_ips()[:5],
            },
            "orchestration": {
                "recent_actions": self.get_orchestrated_actions(limit=5),
                "posture_history": self.get_posture_history(limit=5),
                "config": self.get_config(),
            },
        }


# Global instance
chaitanya = Chaitanya()
