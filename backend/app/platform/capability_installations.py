"""Persistence adapters for organization capability installation state."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import OrganizationCapabilityInstallation
from app.platform.capability_access import CapabilityAccessContext
from app.platform.dominions import CAPABILITY_MANIFESTS, resolve_capability_manifest


class UnknownCapability(ValueError):
    """Raised when an install request references an unknown capability manifest."""


async def install_capability_for_organization(
    db: AsyncSession,
    *,
    organization_id: int,
    capability_id: str,
    actor_user_id: int | None = None,
    granted_permissions: Iterable[str] | None = None,
    data_scopes: Iterable[str] | None = None,
    settings: dict[str, Any] | None = None,
) -> OrganizationCapabilityInstallation:
    """Install or re-enable a capability for one organization."""

    manifest = resolve_capability_manifest(capability_id)
    if manifest is None:
        raise UnknownCapability(f"Unknown capability '{capability_id}'")

    installation = await get_capability_installation(
        db,
        organization_id=organization_id,
        capability_id=capability_id,
    )
    if installation is None:
        installation = OrganizationCapabilityInstallation(
            organization_id=organization_id,
            capability_id=capability_id,
        )
        db.add(installation)

    installation.enabled = True
    installation.lifecycle_state = "installed"
    installation.granted_permissions = list(
        manifest.required_permissions if granted_permissions is None else granted_permissions
    )
    installation.data_scopes = list(manifest.data_scopes if data_scopes is None else data_scopes)
    installation.settings = settings
    installation.installed_by_user_id = actor_user_id
    installation.disabled_by_user_id = None
    installation.disabled_at = None

    await db.flush()
    await db.refresh(installation)
    return installation


async def disable_capability_for_organization(
    db: AsyncSession,
    *,
    organization_id: int,
    capability_id: str,
    actor_user_id: int | None = None,
) -> OrganizationCapabilityInstallation:
    """Disable a previously installed capability without deleting its state."""

    installation = await get_capability_installation(
        db,
        organization_id=organization_id,
        capability_id=capability_id,
    )
    if installation is None:
        raise UnknownCapability(f"Capability '{capability_id}' is not installed")

    installation.enabled = False
    installation.lifecycle_state = "disabled"
    installation.disabled_by_user_id = actor_user_id
    installation.disabled_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(installation)
    return installation


async def get_capability_installation(
    db: AsyncSession,
    *,
    organization_id: int,
    capability_id: str,
) -> OrganizationCapabilityInstallation | None:
    """Return one organization capability installation row if present."""

    result = await db.execute(
        select(OrganizationCapabilityInstallation).where(
            OrganizationCapabilityInstallation.organization_id == organization_id,
            OrganizationCapabilityInstallation.capability_id == capability_id,
        )
    )
    return result.scalar_one_or_none()


async def list_enabled_capability_installations(
    db: AsyncSession,
    *,
    organization_id: int,
) -> list[OrganizationCapabilityInstallation]:
    """Return enabled capability installations for one organization."""

    result = await db.execute(
        select(OrganizationCapabilityInstallation)
        .where(
            OrganizationCapabilityInstallation.organization_id == organization_id,
            OrganizationCapabilityInstallation.enabled.is_(True),
        )
        .order_by(OrganizationCapabilityInstallation.capability_id)
    )
    return list(result.scalars().all())


async def build_persisted_capability_access_context(
    db: AsyncSession,
    actor: Any,
) -> CapabilityAccessContext:
    """Build a pure access context from persisted organization install state."""

    organization_id = int(getattr(actor, "organization_id"))
    installations = await list_enabled_capability_installations(
        db,
        organization_id=organization_id,
    )
    installed_capabilities = tuple(installation.capability_id for installation in installations)
    organization_permissions = _unique(
        permission
        for installation in installations
        for permission in _as_tuple(installation.granted_permissions)
    )
    organization_data_scopes = _unique(
        data_scope
        for installation in installations
        for data_scope in _as_tuple(installation.data_scopes)
    )

    return CapabilityAccessContext(
        organization_id=organization_id,
        user_id=int(getattr(actor, "id", 0) or 0),
        installed_capabilities=installed_capabilities,
        granted_permissions=_effective_permissions(
            actor,
            organization_permissions=organization_permissions,
        ),
        data_scopes=_effective_data_scopes(
            actor,
            organization_data_scopes=organization_data_scopes,
        ),
        roles=_explicit_tuple(actor, "roles") or (),
    )


def _effective_permissions(
    actor: Any,
    *,
    organization_permissions: tuple[str, ...],
) -> tuple[str, ...]:
    if bool(getattr(actor, "is_superuser", False)):
        return _all_manifest_permissions()

    actor_permissions = _explicit_tuple(actor, "granted_permissions", "permissions")
    if actor_permissions is None:
        return organization_permissions
    if _has_global_permission(actor_permissions):
        return organization_permissions
    return _intersect(actor_permissions, organization_permissions)


def _effective_data_scopes(
    actor: Any,
    *,
    organization_data_scopes: tuple[str, ...],
) -> tuple[str, ...]:
    actor_data_scopes = _explicit_tuple(actor, "data_scopes", "data_scope")
    if actor_data_scopes is None:
        return organization_data_scopes
    return _intersect(actor_data_scopes, organization_data_scopes)


def _explicit_tuple(actor: Any, *names: str) -> tuple[str, ...] | None:
    if actor is None:
        return None
    missing = object()
    for name in names:
        value = getattr(actor, name, missing)
        if value is not missing:
            return _as_tuple(value)
    return None


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        return tuple(str(item) for item in value)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values))


def _intersect(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    right_values = set(right)
    return tuple(value for value in left if value in right_values)


def _has_global_permission(permissions: tuple[str, ...]) -> bool:
    return any(permission in {"*", "*:*", "full_access"} for permission in permissions)


def _all_manifest_permissions() -> tuple[str, ...]:
    return _unique(
        permission
        for manifest in CAPABILITY_MANIFESTS.values()
        for permission in manifest.required_permissions
    )
