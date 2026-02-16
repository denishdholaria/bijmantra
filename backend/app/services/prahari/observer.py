"""
DRISHTI (दृष्टि) - The All-Seeing Observer

Multi-layer security observation system.
Watches: Network → Application → Data → User Behavior
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ObservationLayer(str, Enum):
    NETWORK = "network"
    APPLICATION = "application"
    DATA = "data"
    USER_BEHAVIOR = "user_behavior"


class EventSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """A security-relevant event observed by the system."""
    id: str
    timestamp: datetime
    layer: ObservationLayer
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: EventSeverity = EventSeverity.LOW

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "layer": self.layer.value,
            "event_type": self.event_type,
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "details": self.details,
            "severity": self.severity.value,
        }


class SecurityObserver:
    """
    DRISHTI - Multi-layer security observation.
    
    Observes and records security-relevant events across all system layers.
    """

    def __init__(self):
        self._events: List[SecurityEvent] = []
        self._event_counter = 0
        self._observers: Dict[ObservationLayer, List[callable]] = {
            layer: [] for layer in ObservationLayer
        }
        self._rate_limits: Dict[str, List[datetime]] = {}
        self._suspicious_ips: Dict[str, int] = {}
        self._failed_logins: Dict[str, List[datetime]] = {}

    def _generate_event_id(self) -> str:
        self._event_counter += 1
        return f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._event_counter:06d}"

    async def observe_request(
        self,
        endpoint: str,
        method: str,
        source_ip: str,
        user_id: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: float = 0,
        request_size: int = 0,
    ) -> Optional[SecurityEvent]:
        """Observe an API request (Application layer)."""

        event = None
        details = {
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size": request_size,
        }

        # Check for suspicious patterns
        severity = EventSeverity.LOW
        event_type = "api_request"

        # Rate limit check
        if self._check_rate_limit(source_ip, limit=100, window_seconds=60):
            severity = EventSeverity.MEDIUM
            event_type = "rate_limit_exceeded"
            self._suspicious_ips[source_ip] = self._suspicious_ips.get(source_ip, 0) + 1

        # Failed request patterns
        if status_code == 401:
            self._record_failed_login(source_ip)
            if self._check_brute_force(source_ip):
                severity = EventSeverity.HIGH
                event_type = "brute_force_attempt"

        if status_code == 403:
            severity = EventSeverity.MEDIUM
            event_type = "unauthorized_access_attempt"

        # SQL injection patterns in endpoint
        if self._detect_sql_injection(endpoint):
            severity = EventSeverity.CRITICAL
            event_type = "sql_injection_attempt"

        # Large request (potential DoS)
        if request_size > 10_000_000:  # 10MB
            severity = EventSeverity.MEDIUM
            event_type = "large_request"

        # Only record non-trivial events
        if severity != EventSeverity.LOW or status_code >= 400:
            event = SecurityEvent(
                id=self._generate_event_id(),
                timestamp=datetime.now(timezone.utc),
                layer=ObservationLayer.APPLICATION,
                event_type=event_type,
                source_ip=source_ip,
                user_id=user_id,
                endpoint=endpoint,
                details=details,
                severity=severity,
            )
            self._events.append(event)
            await self._notify_observers(ObservationLayer.APPLICATION, event)

        return event

    async def observe_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        source_ip: Optional[str] = None,
    ) -> Optional[SecurityEvent]:
        """Observe data access patterns (Data layer)."""

        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
        }

        severity = EventSeverity.LOW
        event_type = "data_access"

        # Bulk data access
        if action in ["export", "bulk_delete", "bulk_update"]:
            severity = EventSeverity.MEDIUM
            event_type = "bulk_data_operation"

        # Sensitive data access
        if resource_type in ["user", "api_key", "credential", "audit_log"]:
            severity = EventSeverity.MEDIUM
            event_type = "sensitive_data_access"

        if severity != EventSeverity.LOW:
            event = SecurityEvent(
                id=self._generate_event_id(),
                timestamp=datetime.now(timezone.utc),
                layer=ObservationLayer.DATA,
                event_type=event_type,
                source_ip=source_ip,
                user_id=user_id,
                details=details,
                severity=severity,
            )
            self._events.append(event)
            await self._notify_observers(ObservationLayer.DATA, event)
            return event

        return None

    async def observe_user_behavior(
        self,
        user_id: str,
        action: str,
        context: Dict[str, Any],
        source_ip: Optional[str] = None,
    ) -> Optional[SecurityEvent]:
        """Observe user behavior patterns (User Behavior layer)."""

        severity = EventSeverity.LOW
        event_type = "user_action"

        # Unusual time access
        hour = datetime.now(timezone.utc).hour
        if hour < 5 or hour > 23:
            severity = EventSeverity.LOW
            context["unusual_time"] = True

        # Permission escalation attempts
        if action in ["role_change", "permission_grant", "admin_access"]:
            severity = EventSeverity.MEDIUM
            event_type = "privilege_escalation_attempt"

        # Account changes
        if action in ["password_change", "email_change", "mfa_disable"]:
            severity = EventSeverity.MEDIUM
            event_type = "account_security_change"

        if severity != EventSeverity.LOW:
            event = SecurityEvent(
                id=self._generate_event_id(),
                timestamp=datetime.now(timezone.utc),
                layer=ObservationLayer.USER_BEHAVIOR,
                event_type=event_type,
                source_ip=source_ip,
                user_id=user_id,
                details=context,
                severity=severity,
            )
            self._events.append(event)
            await self._notify_observers(ObservationLayer.USER_BEHAVIOR, event)
            return event

        return None

    def _check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if rate limit exceeded."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)

        if key not in self._rate_limits:
            self._rate_limits[key] = []

        # Clean old entries
        self._rate_limits[key] = [t for t in self._rate_limits[key] if t > cutoff]

        # Add current
        self._rate_limits[key].append(now)

        return len(self._rate_limits[key]) > limit

    def _record_failed_login(self, source_ip: str):
        """Record a failed login attempt."""
        now = datetime.now(timezone.utc)
        if source_ip not in self._failed_logins:
            self._failed_logins[source_ip] = []
        self._failed_logins[source_ip].append(now)

    def _check_brute_force(self, source_ip: str, threshold: int = 5, window_minutes: int = 5) -> bool:
        """Check for brute force attack pattern."""
        if source_ip not in self._failed_logins:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        recent = [t for t in self._failed_logins[source_ip] if t > cutoff]
        self._failed_logins[source_ip] = recent

        return len(recent) >= threshold

    def _detect_sql_injection(self, text: str) -> bool:
        """Simple SQL injection pattern detection."""
        patterns = [
            "' OR '1'='1",
            "'; DROP TABLE",
            "UNION SELECT",
            "' OR 1=1--",
            "admin'--",
        ]
        text_upper = text.upper()
        return any(p.upper() in text_upper for p in patterns)

    def register_observer(self, layer: ObservationLayer, callback: callable):
        """Register a callback for events on a specific layer."""
        self._observers[layer].append(callback)

    async def _notify_observers(self, layer: ObservationLayer, event: SecurityEvent):
        """Notify all registered observers of an event."""
        for callback in self._observers[layer]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Observer callback error: {e}")

    def get_recent_events(
        self,
        limit: int = 100,
        layer: Optional[ObservationLayer] = None,
        min_severity: Optional[EventSeverity] = None,
    ) -> List[Dict]:
        """Get recent security events."""
        events = self._events[-limit * 2:]  # Get more to filter

        if layer:
            events = [e for e in events if e.layer == layer]

        if min_severity:
            severity_order = [EventSeverity.LOW, EventSeverity.MEDIUM, EventSeverity.HIGH, EventSeverity.CRITICAL]
            min_idx = severity_order.index(min_severity)
            events = [e for e in events if severity_order.index(e.severity) >= min_idx]

        return [e.to_dict() for e in events[-limit:]]

    def get_suspicious_ips(self) -> Dict[str, int]:
        """Get IPs with suspicious activity counts."""
        return dict(sorted(self._suspicious_ips.items(), key=lambda x: x[1], reverse=True)[:20])

    def get_stats(self) -> Dict:
        """Get observation statistics."""
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        recent_events = [e for e in self._events if e.timestamp > last_hour]
        daily_events = [e for e in self._events if e.timestamp > last_day]

        return {
            "total_events": len(self._events),
            "events_last_hour": len(recent_events),
            "events_last_day": len(daily_events),
            "by_severity": {
                "critical": len([e for e in daily_events if e.severity == EventSeverity.CRITICAL]),
                "high": len([e for e in daily_events if e.severity == EventSeverity.HIGH]),
                "medium": len([e for e in daily_events if e.severity == EventSeverity.MEDIUM]),
                "low": len([e for e in daily_events if e.severity == EventSeverity.LOW]),
            },
            "by_layer": {
                layer.value: len([e for e in daily_events if e.layer == layer])
                for layer in ObservationLayer
            },
            "suspicious_ips_count": len(self._suspicious_ips),
        }


# Global instance
security_observer = SecurityObserver()
