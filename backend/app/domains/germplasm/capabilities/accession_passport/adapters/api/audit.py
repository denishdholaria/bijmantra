"""Audit helpers for Accession Passport API adapters."""

from __future__ import annotations

from typing import Any

from app.domains.germplasm.capabilities.accession_passport.domain import (
    MCPD_AUDIT_TARGET_TYPE,
)
from app.models.audit import AuditLog


async def write_mcpd_audit_event(
    db: Any,
    *,
    organization_id: int | None,
    actor_user_id: int | None,
    action: str,
    changes: dict[str, Any],
    method: str,
    target_id: str | None = None,
) -> None:
    """Write one immutable MCPD audit event to the canonical audit ledger."""

    db.add(
        AuditLog(
            organization_id=organization_id,
            user_id=actor_user_id,
            action=action,
            target_type=MCPD_AUDIT_TARGET_TYPE,
            target_id=target_id,
            changes=changes,
            method=method,
        )
    )
    flush = getattr(db, "flush", None)
    if callable(flush):
        await flush()
