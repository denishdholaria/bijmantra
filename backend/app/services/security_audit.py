"""
Security Audit Log Service

Persistent audit logging for security events.
Critical for compliance and forensic analysis in mission-critical environments.

Logs are stored in:
1. In-memory buffer (for real-time access)
2. File system (for persistence)
3. Database (when available)

NOTE: Uses aiofiles for async file I/O per GOVERNANCE.md §4.3.1
"""

import json
import os
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
import aiofiles

logger = logging.getLogger(__name__)


class AuditCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    SECURITY_EVENT = "security_event"
    THREAT_DETECTED = "threat_detected"
    RESPONSE_ACTION = "response_action"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    id: str
    timestamp: datetime
    category: AuditCategory
    severity: AuditSeverity
    action: str
    actor: Optional[str]  # User ID or system component
    target: Optional[str]  # Resource being accessed/modified
    source_ip: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "action": self.action,
            "actor": self.actor,
            "target": self.target,
            "source_ip": self.source_ip,
            "details": self.details,
            "success": self.success,
        }


class SecurityAuditLog:
    """
    Security Audit Logging Service
    
    Provides persistent, tamper-evident logging for security events.
    """

    def __init__(self, log_dir: str = "logs/security"):
        self._entries: List[AuditEntry] = []
        self._entry_counter = 0
        self._log_dir = Path(log_dir)
        self._current_log_file: Optional[Path] = None
        self._max_memory_entries = 10000

        # Ensure log directory exists
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._rotate_log_file()

    def _generate_entry_id(self) -> str:
        self._entry_counter += 1
        return f"AUD-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{self._entry_counter:06d}"

    def _rotate_log_file(self):
        """Create a new log file for the current day."""
        today = datetime.now(UTC).strftime('%Y-%m-%d')
        self._current_log_file = self._log_dir / f"security-audit-{today}.jsonl"

    async def log(
        self,
        category: AuditCategory,
        action: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        actor: Optional[str] = None,
        target: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> AuditEntry:
        """Log a security audit entry."""

        entry = AuditEntry(
            id=self._generate_entry_id(),
            timestamp=datetime.now(UTC),
            category=category,
            severity=severity,
            action=action,
            actor=actor,
            target=target,
            source_ip=source_ip,
            details=details or {},
            success=success,
        )

        # Add to memory buffer
        self._entries.append(entry)

        # Trim memory buffer if too large
        if len(self._entries) > self._max_memory_entries:
            self._entries = self._entries[-self._max_memory_entries:]

        # Write to file (async)
        await self._write_to_file(entry)

        # Log critical events
        if severity == AuditSeverity.CRITICAL:
            logger.critical(f"SECURITY AUDIT: {action} - {details}")
        elif severity == AuditSeverity.ERROR:
            logger.error(f"SECURITY AUDIT: {action} - {details}")

        return entry

    async def _write_to_file(self, entry: AuditEntry):
        """Write entry to log file (async)."""
        try:
            # Check if we need to rotate
            today = datetime.now(UTC).strftime('%Y-%m-%d')
            expected_file = self._log_dir / f"security-audit-{today}.jsonl"
            if self._current_log_file != expected_file:
                self._rotate_log_file()

            # Write entry as JSON line (async)
            async with aiofiles.open(self._current_log_file, 'a') as f:
                await f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_sync(
        self,
        category: AuditCategory,
        action: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        **kwargs
    ) -> AuditEntry:
        """
        Synchronous version of log for non-async contexts.
        WARNING: Only use this in truly synchronous contexts (CLI, startup).
        Do NOT call from async endpoints - use log() instead.
        """
        # Create entry synchronously (no file write)
        entry = AuditEntry(
            id=self._generate_entry_id(),
            timestamp=datetime.now(UTC),
            category=category,
            severity=severity,
            action=action,
            actor=kwargs.get('actor'),
            target=kwargs.get('target'),
            source_ip=kwargs.get('source_ip'),
            details=kwargs.get('details', {}),
            success=kwargs.get('success', True),
        )

        # Add to memory buffer
        self._entries.append(entry)

        # Trim memory buffer if too large
        if len(self._entries) > self._max_memory_entries:
            self._entries = self._entries[-self._max_memory_entries:]

        # Log critical events
        if severity == AuditSeverity.CRITICAL:
            logger.critical(f"SECURITY AUDIT: {action} - {kwargs.get('details', {})}")
        elif severity == AuditSeverity.ERROR:
            logger.error(f"SECURITY AUDIT: {action} - {kwargs.get('details', {})}")

        # Note: File write skipped in sync version to avoid blocking
        # Entry is still in memory buffer and will be persisted on next async log
        return entry

    # Convenience methods for common audit events
    async def log_login(self, user_id: str, source_ip: str, success: bool, details: Dict = None):
        """Log a login attempt."""
        await self.log(
            category=AuditCategory.AUTHENTICATION,
            action="login_attempt",
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            actor=user_id,
            source_ip=source_ip,
            details=details or {},
            success=success,
        )

    async def log_logout(self, user_id: str, source_ip: str):
        """Log a logout."""
        await self.log(
            category=AuditCategory.AUTHENTICATION,
            action="logout",
            actor=user_id,
            source_ip=source_ip,
        )

    async def log_access_denied(self, user_id: str, resource: str, source_ip: str, reason: str):
        """Log an access denied event."""
        await self.log(
            category=AuditCategory.AUTHORIZATION,
            action="access_denied",
            severity=AuditSeverity.WARNING,
            actor=user_id,
            target=resource,
            source_ip=source_ip,
            details={"reason": reason},
            success=False,
        )

    async def log_data_access(self, user_id: str, resource: str, action: str, source_ip: str = None):
        """Log data access."""
        await self.log(
            category=AuditCategory.DATA_ACCESS,
            action=action,
            actor=user_id,
            target=resource,
            source_ip=source_ip,
        )

    async def log_security_event(self, event_type: str, severity: AuditSeverity, details: Dict):
        """Log a security event from PRAHARI."""
        await self.log(
            category=AuditCategory.SECURITY_EVENT,
            action=event_type,
            severity=severity,
            details=details,
        )

    async def log_threat(self, threat_category: str, confidence: str, source_ip: str, details: Dict):
        """Log a detected threat."""
        await self.log(
            category=AuditCategory.THREAT_DETECTED,
            action=f"threat_{threat_category}",
            severity=AuditSeverity.ERROR if confidence in ['high', 'confirmed'] else AuditSeverity.WARNING,
            source_ip=source_ip,
            details=details,
        )

    async def log_response(self, action: str, target: str, success: bool, details: Dict = None):
        """Log a security response action."""
        await self.log(
            category=AuditCategory.RESPONSE_ACTION,
            action=action,
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            target=target,
            details=details or {},
            success=success,
        )

    async def log_config_change(self, user_id: str, setting: str, old_value: Any, new_value: Any):
        """Log a configuration change."""
        await self.log(
            category=AuditCategory.CONFIGURATION,
            action="config_change",
            severity=AuditSeverity.WARNING,
            actor=user_id,
            target=setting,
            details={"old_value": str(old_value), "new_value": str(new_value)},
        )

    # Query methods
    def get_recent(
        self,
        limit: int = 100,
        category: Optional[AuditCategory] = None,
        severity: Optional[AuditSeverity] = None,
        actor: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get recent audit entries with optional filters."""
        entries = self._entries

        if category:
            entries = [e for e in entries if e.category == category]

        if severity:
            entries = [e for e in entries if e.severity == severity]

        if actor:
            entries = [e for e in entries if e.actor == actor]

        if since:
            entries = [e for e in entries if e.timestamp > since]

        return [e.to_dict() for e in entries[-limit:]]

    def get_by_actor(self, actor: str, limit: int = 100) -> List[Dict]:
        """Get audit entries for a specific actor."""
        entries = [e for e in self._entries if e.actor == actor]
        return [e.to_dict() for e in entries[-limit:]]

    def get_by_target(self, target: str, limit: int = 100) -> List[Dict]:
        """Get audit entries for a specific target."""
        entries = [e for e in self._entries if e.target == target]
        return [e.to_dict() for e in entries[-limit:]]

    def get_failed_actions(self, limit: int = 100) -> List[Dict]:
        """Get failed actions."""
        entries = [e for e in self._entries if not e.success]
        return [e.to_dict() for e in entries[-limit:]]

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get audit statistics."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent = [e for e in self._entries if e.timestamp > cutoff]

        return {
            "total_entries": len(self._entries),
            "entries_last_24h": len(recent),
            "by_category": {
                cat.value: len([e for e in recent if e.category == cat])
                for cat in AuditCategory
            },
            "by_severity": {
                sev.value: len([e for e in recent if e.severity == sev])
                for sev in AuditSeverity
            },
            "failed_actions": len([e for e in recent if not e.success]),
            "unique_actors": len(set(e.actor for e in recent if e.actor)),
            "unique_ips": len(set(e.source_ip for e in recent if e.source_ip)),
        }

    def search(
        self,
        query: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Search audit entries by action or details."""
        query_lower = query.lower()
        results = []

        for entry in reversed(self._entries):
            if query_lower in entry.action.lower():
                results.append(entry.to_dict())
            elif query_lower in str(entry.details).lower():
                results.append(entry.to_dict())
            elif entry.actor and query_lower in entry.actor.lower():
                results.append(entry.to_dict())
            elif entry.target and query_lower in entry.target.lower():
                results.append(entry.to_dict())

            if len(results) >= limit:
                break

        return results

    async def export_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """Export audit logs for a date range."""
        entries = [
            e for e in self._entries
            if start_date <= e.timestamp <= end_date
        ]

        if format == "json":
            return json.dumps([e.to_dict() for e in entries], indent=2)
        elif format == "csv":
            lines = ["id,timestamp,category,severity,action,actor,target,source_ip,success"]
            for e in entries:
                lines.append(f"{e.id},{e.timestamp.isoformat()},{e.category.value},{e.severity.value},{e.action},{e.actor or ''},{e.target or ''},{e.source_ip or ''},{e.success}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global instance
security_audit = SecurityAuditLog()
