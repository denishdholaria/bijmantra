"""
CFR Part 11 Audit Logger Service

Implements the logic for creating and verifying immutable audit trails.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cfr_audit import CFRLog


class CFRPart11AuditLogger:
    """
    Service for managing FDA 21 CFR Part 11 compliant audit logs.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _calculate_hash(self, log_entry: CFRLog) -> str:
        """
        Calculates the SHA256 hash of a log entry.
        The hash includes the previous hash to form a chain.
        """
        # Ensure timestamp is ISO formatted string for consistency
        timestamp_str = log_entry.timestamp.isoformat() if log_entry.timestamp else ""

        # Serialize changes consistently
        changes_str = json.dumps(log_entry.changes, sort_keys=True) if log_entry.changes else ""

        # Data to hash
        data = (
            f"{log_entry.previous_hash}"
            f"{log_entry.user_id}"
            f"{log_entry.organization_id}"
            f"{log_entry.action_type}"
            f"{log_entry.resource_type}"
            f"{log_entry.resource_id}"
            f"{timestamp_str}"
            f"{log_entry.reason or ''}"
            f"{changes_str}"
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def log_action(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
        changes: dict[str, Any] | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> CFRLog:
        """
        Creates a new immutable audit log entry.
        """
        # Fetch the last log entry to link the chain
        # Note: In a high-concurrency environment, this needs strict locking
        # (e.g., SELECT FOR UPDATE) to ensure the chain doesn't fork.
        # For this implementation, we assume standard transaction isolation.
        stmt = select(CFRLog).order_by(CFRLog.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        last_entry = result.scalar_one_or_none()

        previous_hash = last_entry.signature if last_entry else "0" * 64

        # Create the new entry instance
        new_entry = CFRLog(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            organization_id=organization_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            reason=reason,
            ip_address=ip_address,
            previous_hash=previous_hash,
        )

        # Calculate signature
        new_entry.signature = self._calculate_hash(new_entry)

        self.db.add(new_entry)
        await self.db.commit()
        await self.db.refresh(new_entry)

        return new_entry

    async def verify_chain(self) -> bool:
        """
        Verifies the cryptographic integrity of the entire audit log chain.
        Returns True if valid, False if tampering is detected.
        """
        # Fetch all logs ordered by timestamp
        # In a real production system with millions of logs, this would be batched.
        stmt = select(CFRLog).order_by(CFRLog.timestamp.asc())
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        if not logs:
            return True

        previous_hash = "0" * 64

        for log in logs:
            # Check if the log points to the correct previous hash
            if log.previous_hash != previous_hash:
                return False

            # Recalculate hash and verify signature
            calculated_hash = self._calculate_hash(log)
            if calculated_hash != log.signature:
                return False

            previous_hash = log.signature

        return True
