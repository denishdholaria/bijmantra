"""FastAPI-facing guards for platform capability API access.

The pure evaluator lives in ``capability_access``. This module is the thin
HTTP adapter that resolves persisted install state, applies legacy-compatible
actor fallback, and converts denied decisions into a stable 403 payload.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable, SQLAlchemyError

from app.platform.capability_access import (
    CapabilityAccessContext,
    CapabilityAccessDenied,
    require_capability_access,
)
from app.platform.capability_installations import (
    build_persisted_capability_access_context_if_present,
)
from app.platform.dominions import CapabilityManifest, resolve_capability_manifest


_MISSING = object()


async def require_platform_capability_api_access(
    capability_id: str,
    actor: Any,
    *,
    db: Any | None = None,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization",),
    missing_manifest_detail: str | None = None,
) -> None:
    """Reject API access when capability install, permission, or scope denies it.

    Persisted install rows are authoritative when present. Organizations without
    a row still use actor-field fallback so existing local/dev users keep working
    until explicit bootstrap is complete.
    """

    manifest = resolve_capability_manifest(capability_id)
    if manifest is None:
        raise HTTPException(
            status_code=500,
            detail=missing_manifest_detail or f"Capability manifest missing: {capability_id}",
        )

    try:
        require_capability_access(
            manifest,
            await capability_context_from_persistence_or_actor(
                db,
                actor,
                manifest=manifest,
            ),
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


async def capability_context_from_persistence_or_actor(
    db: Any | None,
    actor: Any,
    *,
    manifest: CapabilityManifest,
) -> CapabilityAccessContext:
    """Return persisted capability context when a row exists, otherwise actor fallback."""

    if _supports_async_execute(db):
        persisted_context = await build_persisted_capability_access_context_if_present(
            db,
            actor,
            capability_id=manifest.id,
        )
        if persisted_context is not None:
            return persisted_context
    return capability_context_from_actor(actor, manifest=manifest)


def capability_context_from_actor(
    actor: Any,
    *,
    manifest: CapabilityManifest,
) -> CapabilityAccessContext:
    """Build a capability context from user-like actor fields.

    This is a compatibility adapter for direct unit tests, local superusers, and
    legacy users while the persisted capability install table becomes universal.
    """

    installed_capabilities = _explicit_tuple(
        actor,
        "installed_capabilities",
        "enabled_capabilities",
        "capability_ids",
    )
    if installed_capabilities is None:
        organization = _get_value(actor, "organization", None)
        installed_capabilities = _explicit_tuple(
            organization,
            "installed_capabilities",
            "enabled_capabilities",
            "capability_ids",
        )
    if installed_capabilities is None:
        installed_capabilities = (manifest.id,)

    granted_permissions = _explicit_tuple(actor, "granted_permissions", "permissions")
    if granted_permissions is None or _has_global_permission(granted_permissions):
        granted_permissions = tuple(manifest.required_permissions)

    data_scopes = _explicit_tuple(actor, "data_scopes", "data_scope")
    if data_scopes is None:
        data_scopes = tuple(manifest.data_scopes)

    return CapabilityAccessContext(
        organization_id=int(_get_value(actor, "organization_id")),
        user_id=int(_get_value(actor, "id", 0) or 0),
        installed_capabilities=installed_capabilities,
        granted_permissions=granted_permissions,
        data_scopes=data_scopes,
        roles=_explicit_tuple(actor, "roles") or (),
    )


def _supports_async_execute(db: Any | None) -> bool:
    return callable(getattr(db, "execute", None))


def _explicit_tuple(actor: Any, *names: str) -> tuple[str, ...] | None:
    if actor is None:
        return None
    for name in names:
        value = _get_value(actor, name, _MISSING)
        if value is not _MISSING:
            return _as_tuple(value)
    return None


def _get_value(actor: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(actor, Mapping):
        return actor.get(name, default)
    if _would_lazy_load(actor, name):
        return default
    try:
        return getattr(actor, name, default)
    except SQLAlchemyError:
        return default


def _would_lazy_load(actor: Any, name: str) -> bool:
    """Return true when reading ``name`` would trigger async ORM lazy I/O."""

    try:
        state = inspect(actor)
    except NoInspectionAvailable:
        return False

    unloaded = set(state.unloaded) | set(state.expired_attributes)
    if name in unloaded:
        return True

    if name in {"permissions", "roles"} and "user_roles" in unloaded:
        return True

    return False


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
