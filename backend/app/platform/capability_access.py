"""Pure capability access evaluation for platform app activation.

This module deliberately has no FastAPI, database, or Keycloak dependency.
Route guards can call it later after they load organization install state,
permissions, and policy scopes from infrastructure adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.platform.dominions import CapabilityManifest


CapabilityAccessReason = Literal[
    "allowed",
    "capability_not_installed",
    "missing_permission",
    "missing_data_scope",
]


@dataclass(frozen=True)
class CapabilityAccessContext:
    """Resolved tenant/user capability context for one access check."""

    organization_id: int
    user_id: int
    installed_capabilities: tuple[str, ...]
    granted_permissions: tuple[str, ...]
    data_scopes: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityAccessDecision:
    """Decision returned by pure capability access evaluation."""

    allowed: bool
    reason: CapabilityAccessReason
    capability_id: str
    missing_permissions: tuple[str, ...] = ()
    missing_data_scopes: tuple[str, ...] = ()


class CapabilityAccessDenied(PermissionError):
    """Raised when a caller requests exception-style access enforcement."""

    def __init__(self, decision: CapabilityAccessDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


def evaluate_capability_access(
    manifest: CapabilityManifest,
    context: CapabilityAccessContext,
    *,
    required_permission: str | None = None,
    required_data_scopes: tuple[str, ...] = (),
) -> CapabilityAccessDecision:
    """Return whether a user context can access a capability."""

    if manifest.id not in context.installed_capabilities:
        return CapabilityAccessDecision(
            allowed=False,
            reason="capability_not_installed",
            capability_id=manifest.id,
        )

    missing_permissions = (
        ()
        if required_permission is None or required_permission in context.granted_permissions
        else (required_permission,)
    )
    if missing_permissions:
        return CapabilityAccessDecision(
            allowed=False,
            reason="missing_permission",
            capability_id=manifest.id,
            missing_permissions=missing_permissions,
        )

    missing_data_scopes = tuple(
        data_scope for data_scope in required_data_scopes if data_scope not in context.data_scopes
    )
    if missing_data_scopes:
        return CapabilityAccessDecision(
            allowed=False,
            reason="missing_data_scope",
            capability_id=manifest.id,
            missing_data_scopes=missing_data_scopes,
        )

    return CapabilityAccessDecision(
        allowed=True,
        reason="allowed",
        capability_id=manifest.id,
    )


def require_capability_access(
    manifest: CapabilityManifest,
    context: CapabilityAccessContext,
    *,
    required_permission: str | None = None,
    required_data_scopes: tuple[str, ...] = (),
) -> CapabilityAccessDecision:
    """Return an allowed decision or raise ``CapabilityAccessDenied``."""

    decision = evaluate_capability_access(
        manifest,
        context,
        required_permission=required_permission,
        required_data_scopes=required_data_scopes,
    )
    if not decision.allowed:
        raise CapabilityAccessDenied(decision)
    return decision
