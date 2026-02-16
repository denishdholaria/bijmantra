"""
VIVEK (विवेक) - The Discriminator / Threat Analyzer

Analyzes security events to determine threat level and classification.
Friend or foe detection with contextual intelligence.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from .observer import SecurityEvent, EventSeverity, ObservationLayer

logger = logging.getLogger(__name__)


class ThreatCategory(str, Enum):
    RECONNAISSANCE = "reconnaissance"  # Scanning, probing
    BRUTE_FORCE = "brute_force"  # Password attacks
    INJECTION = "injection"  # SQL, XSS, command injection
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    DENIAL_OF_SERVICE = "denial_of_service"
    INSIDER_THREAT = "insider_threat"
    UNKNOWN = "unknown"


class ThreatConfidence(str, Enum):
    LOW = "low"  # < 40%
    MEDIUM = "medium"  # 40-70%
    HIGH = "high"  # 70-90%
    CONFIRMED = "confirmed"  # > 90%


@dataclass
class ThreatAssessment:
    """Result of threat analysis on a security event."""
    id: str
    event_id: str
    timestamp: datetime
    category: ThreatCategory
    confidence: ThreatConfidence
    confidence_score: float  # 0-100
    severity: EventSeverity
    indicators: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "severity": self.severity.value,
            "indicators": self.indicators,
            "recommended_actions": self.recommended_actions,
            "context": self.context,
        }


class ThreatAnalyzer:
    """
    VIVEK - Threat analysis and classification engine.
    
    Analyzes security events to determine:
    - Threat category (what type of attack)
    - Confidence level (how sure are we)
    - Severity (how bad is it)
    - Recommended response actions
    """

    def __init__(self):
        self._assessments: List[ThreatAssessment] = []
        self._assessment_counter = 0
        self._threat_patterns: Dict[str, List[str]] = {}
        self._known_bad_ips: set = set()
        self._known_good_ips: set = {"127.0.0.1", "::1"}
        self._ip_reputation: Dict[str, float] = {}  # IP -> score (0-100, higher = more suspicious)

    def _generate_assessment_id(self) -> str:
        self._assessment_counter += 1
        return f"THR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._assessment_counter:06d}"

    async def analyze(self, event: SecurityEvent) -> ThreatAssessment:
        """Analyze a security event and produce threat assessment."""

        # Determine threat category
        category = self._classify_threat(event)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(event, category)
        confidence = self._score_to_confidence(confidence_score)

        # Determine severity (may upgrade from event severity)
        severity = self._assess_severity(event, category, confidence_score)

        # Gather indicators
        indicators = self._gather_indicators(event, category)

        # Generate recommended actions
        actions = self._recommend_actions(category, severity, confidence)

        # Build context
        context = self._build_context(event)

        assessment = ThreatAssessment(
            id=self._generate_assessment_id(),
            event_id=event.id,
            timestamp=datetime.now(timezone.utc),
            category=category,
            confidence=confidence,
            confidence_score=confidence_score,
            severity=severity,
            indicators=indicators,
            recommended_actions=actions,
            context=context,
        )

        self._assessments.append(assessment)

        # Update IP reputation
        if event.source_ip:
            self._update_ip_reputation(event.source_ip, confidence_score)

        return assessment

    def _classify_threat(self, event: SecurityEvent) -> ThreatCategory:
        """Classify the type of threat based on event characteristics."""

        event_type = event.event_type.lower()

        # Injection attacks
        if "injection" in event_type or "xss" in event_type:
            return ThreatCategory.INJECTION

        # Brute force
        if "brute_force" in event_type or "failed_login" in event_type:
            return ThreatCategory.BRUTE_FORCE

        # Rate limiting / DoS
        if "rate_limit" in event_type or "large_request" in event_type:
            return ThreatCategory.DENIAL_OF_SERVICE

        # Unauthorized access
        if "unauthorized" in event_type or "privilege" in event_type:
            return ThreatCategory.PRIVILEGE_ESCALATION

        # Data access patterns
        if event.layer == ObservationLayer.DATA:
            if event.event_type in ["bulk_data_operation", "sensitive_data_access"]:
                return ThreatCategory.DATA_EXFILTRATION

        # User behavior anomalies
        if event.layer == ObservationLayer.USER_BEHAVIOR:
            if "account_security_change" in event_type:
                return ThreatCategory.INSIDER_THREAT

        return ThreatCategory.UNKNOWN

    def _calculate_confidence(self, event: SecurityEvent, category: ThreatCategory) -> float:
        """Calculate confidence score (0-100) for the threat assessment."""

        score = 30.0  # Base score

        # Event severity contributes
        severity_scores = {
            EventSeverity.LOW: 10,
            EventSeverity.MEDIUM: 25,
            EventSeverity.HIGH: 40,
            EventSeverity.CRITICAL: 50,
        }
        score += severity_scores.get(event.severity, 0)

        # Known bad IP
        if event.source_ip in self._known_bad_ips:
            score += 30

        # IP reputation
        if event.source_ip and event.source_ip in self._ip_reputation:
            score += self._ip_reputation[event.source_ip] * 0.2

        # Multiple indicators
        if len(event.details) > 3:
            score += 10

        # Specific event types are more certain
        certain_types = ["sql_injection_attempt", "brute_force_attempt"]
        if event.event_type in certain_types:
            score += 20

        return min(100.0, score)

    def _score_to_confidence(self, score: float) -> ThreatConfidence:
        """Convert numeric score to confidence level."""
        if score >= 90:
            return ThreatConfidence.CONFIRMED
        elif score >= 70:
            return ThreatConfidence.HIGH
        elif score >= 40:
            return ThreatConfidence.MEDIUM
        return ThreatConfidence.LOW

    def _assess_severity(self, event: SecurityEvent, category: ThreatCategory,
                        confidence: float) -> EventSeverity:
        """Assess final severity, potentially upgrading from event severity."""

        severity = event.severity

        # High confidence threats get severity bump
        if confidence >= 70:
            if severity == EventSeverity.LOW:
                severity = EventSeverity.MEDIUM
            elif severity == EventSeverity.MEDIUM:
                severity = EventSeverity.HIGH

        # Certain categories are always high severity
        critical_categories = [ThreatCategory.INJECTION, ThreatCategory.DATA_EXFILTRATION]
        if category in critical_categories and severity != EventSeverity.CRITICAL:
            severity = EventSeverity.HIGH

        return severity

    def _gather_indicators(self, event: SecurityEvent, category: ThreatCategory) -> List[str]:
        """Gather indicators of compromise (IOCs)."""

        indicators = []

        if event.source_ip:
            indicators.append(f"Source IP: {event.source_ip}")

        if event.user_id:
            indicators.append(f"User: {event.user_id}")

        if event.endpoint:
            indicators.append(f"Endpoint: {event.endpoint}")

        indicators.append(f"Event type: {event.event_type}")
        indicators.append(f"Layer: {event.layer.value}")

        # Category-specific indicators
        if category == ThreatCategory.BRUTE_FORCE:
            indicators.append("Multiple failed authentication attempts")
        elif category == ThreatCategory.INJECTION:
            indicators.append("Malicious payload detected in request")
        elif category == ThreatCategory.DENIAL_OF_SERVICE:
            indicators.append("Abnormal request volume or size")

        return indicators

    def _recommend_actions(self, category: ThreatCategory, severity: EventSeverity,
                          confidence: ThreatConfidence) -> List[str]:
        """Generate recommended response actions."""

        actions = []

        # Always log
        actions.append("Log incident for audit trail")

        # Severity-based actions
        if severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
            actions.append("Alert security team immediately")

        if severity == EventSeverity.CRITICAL:
            actions.append("Consider blocking source IP")

        # Category-specific actions
        category_actions = {
            ThreatCategory.BRUTE_FORCE: [
                "Implement account lockout",
                "Add CAPTCHA to login",
                "Rate limit authentication endpoint",
            ],
            ThreatCategory.INJECTION: [
                "Block request immediately",
                "Review and sanitize input validation",
                "Scan for similar patterns in logs",
            ],
            ThreatCategory.DENIAL_OF_SERVICE: [
                "Apply rate limiting",
                "Enable DDoS protection",
                "Scale infrastructure if needed",
            ],
            ThreatCategory.PRIVILEGE_ESCALATION: [
                "Revoke suspicious session",
                "Audit user permissions",
                "Review access logs",
            ],
            ThreatCategory.DATA_EXFILTRATION: [
                "Block data transfer",
                "Revoke user access",
                "Forensic analysis of accessed data",
            ],
            ThreatCategory.INSIDER_THREAT: [
                "Monitor user activity closely",
                "Review recent account changes",
                "Contact user for verification",
            ],
        }

        actions.extend(category_actions.get(category, []))

        # Confidence-based actions
        if confidence == ThreatConfidence.CONFIRMED:
            actions.insert(1, "Initiate incident response procedure")

        return actions

    def _build_context(self, event: SecurityEvent) -> Dict[str, Any]:
        """Build contextual information for the assessment."""

        context = {
            "event_details": event.details,
            "timestamp": event.timestamp.isoformat(),
        }

        if event.source_ip:
            context["ip_reputation"] = self._ip_reputation.get(event.source_ip, 0)
            context["ip_known_bad"] = event.source_ip in self._known_bad_ips

        return context

    def _update_ip_reputation(self, ip: str, threat_score: float):
        """Update IP reputation based on threat assessment."""

        if ip in self._known_good_ips:
            return

        current = self._ip_reputation.get(ip, 0)
        # Weighted average, recent events have more weight
        self._ip_reputation[ip] = min(100, current * 0.7 + threat_score * 0.3)

        # Auto-add to known bad if reputation is very high
        if self._ip_reputation[ip] >= 90:
            self._known_bad_ips.add(ip)

    def add_known_bad_ip(self, ip: str):
        """Manually add an IP to the known bad list."""
        self._known_bad_ips.add(ip)
        self._ip_reputation[ip] = 100

    def add_known_good_ip(self, ip: str):
        """Manually add an IP to the known good list."""
        self._known_good_ips.add(ip)
        if ip in self._known_bad_ips:
            self._known_bad_ips.remove(ip)
        if ip in self._ip_reputation:
            del self._ip_reputation[ip]

    def get_recent_assessments(self, limit: int = 100,
                               min_confidence: Optional[ThreatConfidence] = None) -> List[Dict]:
        """Get recent threat assessments."""

        assessments = self._assessments[-limit * 2:]

        if min_confidence:
            confidence_order = [ThreatConfidence.LOW, ThreatConfidence.MEDIUM,
                              ThreatConfidence.HIGH, ThreatConfidence.CONFIRMED]
            min_idx = confidence_order.index(min_confidence)
            assessments = [a for a in assessments
                          if confidence_order.index(a.confidence) >= min_idx]

        return [a.to_dict() for a in assessments[-limit:]]

    def get_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Get reputation information for an IP."""
        return {
            "ip": ip,
            "reputation_score": self._ip_reputation.get(ip, 0),
            "known_bad": ip in self._known_bad_ips,
            "known_good": ip in self._known_good_ips,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get threat analysis statistics."""

        now = datetime.now(timezone.utc)
        last_day = now - timedelta(days=1)
        recent = [a for a in self._assessments if a.timestamp > last_day]

        return {
            "total_assessments": len(self._assessments),
            "assessments_24h": len(recent),
            "by_category": {
                cat.value: len([a for a in recent if a.category == cat])
                for cat in ThreatCategory
            },
            "by_confidence": {
                conf.value: len([a for a in recent if a.confidence == conf])
                for conf in ThreatConfidence
            },
            "known_bad_ips": len(self._known_bad_ips),
            "tracked_ips": len(self._ip_reputation),
        }


# Global instance
threat_analyzer = ThreatAnalyzer()
