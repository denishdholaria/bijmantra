"""
SHAKTI (शक्ति) - The Power / Threat Responder

Active countermeasures and automated response to security threats.
Includes KAVACH (Shield) for passive protection and MAYA (Illusion) for deception.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from .threat_analyzer import ThreatAssessment, ThreatCategory, ThreatConfidence
from .observer import EventSeverity

logger = logging.getLogger(__name__)


class ResponseAction(str, Enum):
    LOG = "log"  # Just log the incident
    ALERT = "alert"  # Send alert to security team
    RATE_LIMIT = "rate_limit"  # Apply rate limiting
    BLOCK_IP = "block_ip"  # Block source IP
    BLOCK_USER = "block_user"  # Block user account
    CAPTCHA = "captcha"  # Require CAPTCHA
    MFA_CHALLENGE = "mfa_challenge"  # Force MFA re-verification
    SESSION_REVOKE = "session_revoke"  # Revoke user session
    HONEYPOT = "honeypot"  # Redirect to honeypot (MAYA)
    TARPIT = "tarpit"  # Slow down responses (MAYA)


class ResponseStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResponseRecord:
    """Record of a response action taken."""
    id: str
    assessment_id: str
    action: ResponseAction
    status: ResponseStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    target: Optional[str] = None  # IP, user_id, etc.
    duration_seconds: Optional[int] = None  # For time-limited actions
    result: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "action": self.action.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "target": self.target,
            "duration_seconds": self.duration_seconds,
            "result": self.result,
            "details": self.details,
        }


class ThreatResponder:
    """
    SHAKTI - Automated threat response system.
    
    Executes countermeasures based on threat assessments.
    Includes KAVACH (passive shields) and MAYA (deception).
    """
    
    def __init__(self):
        self._responses: List[ResponseRecord] = []
        self._response_counter = 0
        self._blocked_ips: Dict[str, datetime] = {}  # IP -> expiry time
        self._blocked_users: Dict[str, datetime] = {}  # user_id -> expiry time
        self._rate_limited: Dict[str, Dict] = {}  # key -> {limit, window, expiry}
        self._honeypot_targets: set = set()  # IPs redirected to honeypot
        
        # Response handlers
        self._handlers: Dict[ResponseAction, Callable] = {
            ResponseAction.LOG: self._handle_log,
            ResponseAction.ALERT: self._handle_alert,
            ResponseAction.RATE_LIMIT: self._handle_rate_limit,
            ResponseAction.BLOCK_IP: self._handle_block_ip,
            ResponseAction.BLOCK_USER: self._handle_block_user,
            ResponseAction.CAPTCHA: self._handle_captcha,
            ResponseAction.SESSION_REVOKE: self._handle_session_revoke,
            ResponseAction.HONEYPOT: self._handle_honeypot,
            ResponseAction.TARPIT: self._handle_tarpit,
        }
        
        # Auto-response rules based on threat category and severity
        self._auto_response_rules = {
            (ThreatCategory.INJECTION, EventSeverity.CRITICAL): [
                ResponseAction.BLOCK_IP, ResponseAction.ALERT
            ],
            (ThreatCategory.INJECTION, EventSeverity.HIGH): [
                ResponseAction.RATE_LIMIT, ResponseAction.ALERT
            ],
            (ThreatCategory.BRUTE_FORCE, EventSeverity.HIGH): [
                ResponseAction.BLOCK_IP, ResponseAction.CAPTCHA
            ],
            (ThreatCategory.BRUTE_FORCE, EventSeverity.MEDIUM): [
                ResponseAction.RATE_LIMIT, ResponseAction.CAPTCHA
            ],
            (ThreatCategory.DENIAL_OF_SERVICE, EventSeverity.CRITICAL): [
                ResponseAction.BLOCK_IP, ResponseAction.ALERT
            ],
            (ThreatCategory.DENIAL_OF_SERVICE, EventSeverity.HIGH): [
                ResponseAction.RATE_LIMIT
            ],
            (ThreatCategory.PRIVILEGE_ESCALATION, EventSeverity.HIGH): [
                ResponseAction.SESSION_REVOKE, ResponseAction.ALERT
            ],
            (ThreatCategory.DATA_EXFILTRATION, EventSeverity.CRITICAL): [
                ResponseAction.BLOCK_USER, ResponseAction.ALERT
            ],
            (ThreatCategory.INSIDER_THREAT, EventSeverity.HIGH): [
                ResponseAction.ALERT, ResponseAction.LOG
            ],
        }
    
    def _generate_response_id(self) -> str:
        self._response_counter += 1
        return f"RSP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._response_counter:06d}"

    async def respond(self, assessment: ThreatAssessment, 
                     actions: Optional[List[ResponseAction]] = None,
                     params: Optional[Dict[str, Any]] = None) -> List[ResponseRecord]:
        """Execute response actions for a threat assessment."""
        
        # Use auto-response rules if no actions specified
        if actions is None:
            actions = self._get_auto_responses(assessment)
        
        if not actions:
            actions = [ResponseAction.LOG]  # Always at least log
        
        records = []
        params = params or {}
        
        for action in actions:
            record = await self._execute_action(assessment, action, params)
            records.append(record)
        
        return records
    
    def _get_auto_responses(self, assessment: ThreatAssessment) -> List[ResponseAction]:
        """Get automatic response actions based on threat assessment."""
        
        key = (assessment.category, assessment.severity)
        actions = self._auto_response_rules.get(key, [])
        
        # Always log high-confidence threats
        if assessment.confidence in [ThreatConfidence.HIGH, ThreatConfidence.CONFIRMED]:
            if ResponseAction.LOG not in actions:
                actions = [ResponseAction.LOG] + list(actions)
        
        return actions
    
    async def _execute_action(self, assessment: ThreatAssessment, 
                             action: ResponseAction,
                             params: Dict[str, Any]) -> ResponseRecord:
        """Execute a single response action."""
        
        record = ResponseRecord(
            id=self._generate_response_id(),
            assessment_id=assessment.id,
            action=action,
            status=ResponseStatus.EXECUTING,
            started_at=datetime.now(timezone.utc),
            target=params.get("target") or assessment.context.get("source_ip"),
            duration_seconds=params.get("duration_seconds", 3600),
            details=params,
        )
        
        try:
            handler = self._handlers.get(action)
            if handler:
                result = await handler(assessment, params)
                record.status = ResponseStatus.SUCCESS
                record.result = result
            else:
                record.status = ResponseStatus.SKIPPED
                record.result = f"No handler for action: {action.value}"
        except Exception as e:
            record.status = ResponseStatus.FAILED
            record.result = str(e)
            logger.error(f"Response action failed: {action.value} - {e}")
        
        record.completed_at = datetime.now(timezone.utc)
        self._responses.append(record)
        return record
    
    # Response handlers
    async def _handle_log(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Log the security incident."""
        logger.warning(f"Security incident: {assessment.category.value} - "
                      f"Severity: {assessment.severity.value} - "
                      f"Confidence: {assessment.confidence.value}")
        return "Incident logged"
    
    async def _handle_alert(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Send alert to security team."""
        # In production, this would send email/Slack/PagerDuty
        logger.critical(f"SECURITY ALERT: {assessment.category.value} threat detected!")
        return "Alert sent to security team"
    
    async def _handle_rate_limit(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Apply rate limiting to source."""
        target = params.get("target") or assessment.context.get("source_ip", "unknown")
        duration = params.get("duration_seconds", 300)
        limit = params.get("requests_per_minute", 10)
        
        self._rate_limited[target] = {
            "limit": limit,
            "window": 60,
            "expiry": datetime.now(timezone.utc) + timedelta(seconds=duration),
        }
        return f"Rate limit applied to {target}: {limit} req/min for {duration}s"
    
    async def _handle_block_ip(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Block source IP address."""
        ip = params.get("target") or assessment.context.get("source_ip")
        if not ip:
            return "No IP to block"
        
        duration = params.get("duration_seconds", 3600)
        self._blocked_ips[ip] = datetime.now(timezone.utc) + timedelta(seconds=duration)
        return f"IP {ip} blocked for {duration}s"

    async def _handle_block_user(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Block user account."""
        user_id = params.get("target") or assessment.context.get("user_id")
        if not user_id:
            return "No user to block"
        
        duration = params.get("duration_seconds", 86400)  # 24 hours default
        self._blocked_users[user_id] = datetime.now(timezone.utc) + timedelta(seconds=duration)
        return f"User {user_id} blocked for {duration}s"
    
    async def _handle_captcha(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Require CAPTCHA for source."""
        # In production, this would set a flag requiring CAPTCHA
        return "CAPTCHA requirement enabled"
    
    async def _handle_session_revoke(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Revoke user session."""
        user_id = params.get("target") or assessment.context.get("user_id")
        if not user_id:
            return "No user session to revoke"
        # In production, this would invalidate JWT tokens
        return f"Session revoked for user {user_id}"
    
    async def _handle_honeypot(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Redirect attacker to honeypot (MAYA - Illusion)."""
        ip = params.get("target") or assessment.context.get("source_ip")
        if ip:
            self._honeypot_targets.add(ip)
            return f"IP {ip} redirected to honeypot"
        return "No target for honeypot"
    
    async def _handle_tarpit(self, assessment: ThreatAssessment, params: Dict) -> str:
        """Slow down responses to attacker (MAYA - Illusion)."""
        # In production, this would add artificial delays
        delay_ms = params.get("delay_ms", 5000)
        return f"Tarpit enabled with {delay_ms}ms delay"
    
    # Query methods
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is currently blocked."""
        if ip not in self._blocked_ips:
            return False
        if datetime.now(timezone.utc) > self._blocked_ips[ip]:
            del self._blocked_ips[ip]
            return False
        return True
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if a user is currently blocked."""
        if user_id not in self._blocked_users:
            return False
        if datetime.now(timezone.utc) > self._blocked_users[user_id]:
            del self._blocked_users[user_id]
            return False
        return True
    
    def get_rate_limit(self, key: str) -> Optional[Dict]:
        """Get rate limit for a key if active."""
        if key not in self._rate_limited:
            return None
        if datetime.now(timezone.utc) > self._rate_limited[key]["expiry"]:
            del self._rate_limited[key]
            return None
        return self._rate_limited[key]
    
    def is_honeypot_target(self, ip: str) -> bool:
        """Check if IP should be redirected to honeypot."""
        return ip in self._honeypot_targets
    
    def unblock_ip(self, ip: str) -> bool:
        """Manually unblock an IP."""
        if ip in self._blocked_ips:
            del self._blocked_ips[ip]
            return True
        return False
    
    def unblock_user(self, user_id: str) -> bool:
        """Manually unblock a user."""
        if user_id in self._blocked_users:
            del self._blocked_users[user_id]
            return True
        return False
    
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of currently blocked IPs."""
        now = datetime.now(timezone.utc)
        # Clean expired
        self._blocked_ips = {k: v for k, v in self._blocked_ips.items() if v > now}
        return [
            {"ip": ip, "expires_at": exp.isoformat(), 
             "remaining_seconds": int((exp - now).total_seconds())}
            for ip, exp in self._blocked_ips.items()
        ]
    
    def get_blocked_users(self) -> List[Dict[str, Any]]:
        """Get list of currently blocked users."""
        now = datetime.now(timezone.utc)
        self._blocked_users = {k: v for k, v in self._blocked_users.items() if v > now}
        return [
            {"user_id": uid, "expires_at": exp.isoformat(),
             "remaining_seconds": int((exp - now).total_seconds())}
            for uid, exp in self._blocked_users.items()
        ]
    
    def get_response_history(self, limit: int = 100) -> List[Dict]:
        """Get recent response actions."""
        sorted_responses = sorted(self._responses, key=lambda x: x.started_at, reverse=True)
        return [r.to_dict() for r in sorted_responses[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get response statistics."""
        now = datetime.now(timezone.utc)
        last_day = now - timedelta(days=1)
        recent = [r for r in self._responses if r.started_at > last_day]
        
        return {
            "total_responses": len(self._responses),
            "responses_24h": len(recent),
            "blocked_ips": len(self._blocked_ips),
            "blocked_users": len(self._blocked_users),
            "rate_limited": len(self._rate_limited),
            "honeypot_targets": len(self._honeypot_targets),
            "by_action": {
                action.value: len([r for r in recent if r.action == action])
                for action in ResponseAction
            },
            "by_status": {
                status.value: len([r for r in recent if r.status == status])
                for status in ResponseStatus
            },
        }


# Global instance
threat_responder = ThreatResponder()
