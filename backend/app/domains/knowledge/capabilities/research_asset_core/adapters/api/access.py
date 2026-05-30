"""FastAPI access guard for ResearchAsset capability APIs."""

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


RESEARCH_ASSET_CAPABILITY_ID = "scientific_publishing_fair_exchange.research_asset_core"
_MISSING = object()


def require_research_asset_api_access(
    actor: Any,
    *,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization",),
) -> None:
    """Reject API access when the ResearchAsset capability context denies it.

    Until organization install state is persisted, older user objects without
    explicit capability fields are treated as legacy-compatible installed users.
    Tests and future adapters can pass explicit empty capability/permission
    fields to prove disabled or unauthorized access is rejected.
    """

    manifest = resolve_capability_manifest(RESEARCH_ASSET_CAPABILITY_ID)
    if manifest is None:
        raise HTTPException(status_code=500, detail="ResearchAsset capability manifest missing")

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
    if granted_permissions is None:
        granted_permissions = _all_research_asset_permissions(actor)
    elif _has_global_permission(granted_permissions):
        granted_permissions = _all_research_asset_permissions(actor)

    data_scopes = _explicit_tuple(actor, "data_scopes", "data_scope")
    if data_scopes is None:
        data_scopes = (
            "organization",
            "asset",
            "provenance",
            "license",
            "identifier",
            "connector",
            "evidence",
        )

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


def _all_research_asset_permissions(actor: Any) -> tuple[str, ...]:
    if bool(getattr(actor, "is_superuser", False)):
        return (
            "research_assets.read",
            "research_assets.register",
            "research_assets.promote_fair",
        )
    return (
        "research_assets.read",
        "research_assets.register",
        "research_assets.promote_fair",
    )
