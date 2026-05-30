"""FastAPI access guard for Knowledge Graph capability APIs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException

from app.platform.capability_access import (
    CapabilityAccessContext,
    CapabilityAccessDenied,
    require_capability_access,
)
from app.platform.dominions import resolve_capability_manifest


KNOWLEDGE_GRAPH_CAPABILITY_ID = "intelligence_fabric.knowledge_graph"
_MISSING = object()


def require_knowledge_graph_api_access(
    actor: Any,
    *,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization",),
) -> None:
    """Reject API access when the Knowledge Graph capability context denies it.

    Current production user objects do not yet carry persisted capability
    install state, so missing capability fields remain legacy-compatible.
    Explicit empty fields in tests or future adapters are treated as denial.
    """

    manifest = resolve_capability_manifest(KNOWLEDGE_GRAPH_CAPABILITY_ID)
    if manifest is None:
        raise HTTPException(status_code=500, detail="Knowledge Graph capability manifest missing")

    try:
        require_capability_access(
            manifest,
            _capability_context_from_actor(actor, manifest_id=manifest.id),
            required_permission=required_permission,
            required_data_scopes=required_data_scopes,
        )
    except CapabilityAccessDenied as error:
        raise HTTPException(
            status_code=403,
            detail={
                "reason": error.decision.reason,
                "capabilityId": error.decision.capability_id,
                "missingPermissions": list(error.decision.missing_permissions),
                "missingDataScopes": list(error.decision.missing_data_scopes),
            },
        ) from error


def _capability_context_from_actor(
    actor: Any,
    *,
    manifest_id: str,
) -> CapabilityAccessContext:
    installed_capabilities = _explicit_tuple(
        actor,
        "installed_capabilities",
        "enabled_capabilities",
        "capability_ids",
    )
    if installed_capabilities is None:
        organization = getattr(actor, "organization", None)
        installed_capabilities = _explicit_tuple(
            organization,
            "installed_capabilities",
            "enabled_capabilities",
            "capability_ids",
        )
    if installed_capabilities is None:
        installed_capabilities = (manifest_id,)

    granted_permissions = _explicit_tuple(actor, "granted_permissions", "permissions")
    if granted_permissions is None or _has_global_permission(granted_permissions):
        granted_permissions = _all_knowledge_graph_permissions()

    data_scopes = _explicit_tuple(actor, "data_scopes", "data_scope")
    if data_scopes is None:
        data_scopes = ("organization", "asset", "evidence", "provenance")

    return CapabilityAccessContext(
        organization_id=int(getattr(actor, "organization_id")),
        user_id=int(getattr(actor, "id", 0) or 0),
        installed_capabilities=installed_capabilities,
        granted_permissions=granted_permissions,
        data_scopes=data_scopes,
        roles=_explicit_tuple(actor, "roles") or (),
    )


def _explicit_tuple(actor: Any, *names: str) -> tuple[str, ...] | None:
    if actor is None:
        return None
    for name in names:
        value = getattr(actor, name, _MISSING)
        if value is not _MISSING:
            return _as_tuple(value)
    return None


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


def _has_global_permission(permissions: tuple[str, ...]) -> bool:
    return any(permission in {"*", "*:*", "full_access"} for permission in permissions)


def _all_knowledge_graph_permissions() -> tuple[str, ...]:
    return (
        "intelligence.knowledge_graph.read",
        "intelligence.knowledge_graph.write",
    )
