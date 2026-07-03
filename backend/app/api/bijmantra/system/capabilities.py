"""Platform capability-app management API.

This is an internal system control surface for tenant-scoped capability
activation. Product APIs remain owned by their capability packs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_current_user
from app.core.database import get_db
from app.models.core import User
from app.models.platform import OrganizationCapabilityInstallation
from app.platform.capability_access import (
    CapabilityAccessDecision,
    CapabilityAccessReason,
    evaluate_capability_manifest_access,
)
from app.platform.capability_bootstrap import (
    FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS,
    CapabilityBootstrapReceipt,
    bootstrap_capability_installations,
)
from app.platform.capability_installations import (
    UnknownCapability,
    build_persisted_capability_access_context,
    disable_capability_for_organization,
    get_capability_installation,
    install_capability_for_organization,
    list_capability_installations,
)
from app.platform.dominions import (
    CAPABILITY_MANIFESTS,
    CapabilityManifest,
    resolve_capability_manifest,
)


router = APIRouter(prefix="/system/capabilities", tags=["Platform Capabilities"])
current_user_router = APIRouter(prefix="/platform/capabilities", tags=["Platform Capabilities"])


class CapabilityManifestResponse(BaseModel):
    id: str
    title: str
    dominion: str
    owner_domain: str
    supporting_domains: tuple[str, ...]
    lifecycle: str
    standards: tuple[str, ...]
    frontend_routes: tuple[str, ...]
    backend_routes: tuple[str, ...]
    data_scopes: tuple[str, ...]
    required_permissions: tuple[str, ...]
    suggested_roles: tuple[str, ...]
    semantic_spine_adrs: tuple[str, ...]
    install_behavior: str
    uninstall_behavior: str
    tests: tuple[str, ...]
    audit_events: tuple[str, ...]
    source_context: tuple[str, ...]
    backend_code_root: str | None = None
    frontend_code_root: str | None = None


class CapabilityInstallationResponse(BaseModel):
    capability_id: str
    organization_id: int
    enabled: bool
    lifecycle_state: str
    granted_permissions: list[str]
    data_scopes: list[str]
    settings: dict[str, Any] | None = None
    installed_by_user_id: int | None = None
    disabled_by_user_id: int | None = None
    disabled_at: datetime | None = None


class CapabilityStateResponse(BaseModel):
    manifest: CapabilityManifestResponse
    installation: CapabilityInstallationResponse | None = None


class CapabilityInstallRequest(BaseModel):
    organization_id: int | None = Field(default=None, ge=1)
    granted_permissions: list[str] | None = None
    data_scopes: list[str] | None = None
    settings: dict[str, Any] | None = None


class CapabilityDisableRequest(BaseModel):
    organization_id: int | None = Field(default=None, ge=1)


class CapabilityBootstrapRequest(BaseModel):
    organization_id: int | None = Field(default=None, ge=1)
    capability_ids: list[str] | None = None


class CapabilityBootstrapReceiptResponse(BaseModel):
    capability_id: str
    organization_id: int
    action: str
    enabled: bool
    lifecycle_state: str


class CapabilityBootstrapResponse(BaseModel):
    organization_id: int
    default_capability_ids: tuple[str, ...]
    receipts: list[CapabilityBootstrapReceiptResponse]


class CapabilityManifestListResponse(BaseModel):
    capabilities: list[CapabilityManifestResponse]


class CapabilityInstallationListResponse(BaseModel):
    organization_id: int
    installations: list[CapabilityInstallationResponse]


class CurrentCapabilityOrganizationResponse(BaseModel):
    id: int


class CapabilityAccessDecisionResponse(BaseModel):
    capability_id: str
    allowed: bool
    reason: CapabilityAccessReason
    missing_permissions: list[str]
    missing_data_scopes: list[str]


class CurrentUserCapabilityContextResponse(BaseModel):
    current_organization: CurrentCapabilityOrganizationResponse
    organization_id: int
    user_id: int
    installed_capability_ids: list[str]
    enabled_capability_ids: list[str]
    granted_permissions: list[str]
    data_scopes: list[str]
    roles: list[str]
    capability_decisions: list[CapabilityAccessDecisionResponse]


@current_user_router.get("/me", response_model=CurrentUserCapabilityContextResponse)
async def get_current_user_capability_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentUserCapabilityContextResponse:
    """Return the current authenticated user's platform capability context."""

    context = await build_persisted_capability_access_context(db, current_user)
    installations = await list_capability_installations(
        db,
        organization_id=context.organization_id,
    )
    decisions = [
        evaluate_capability_manifest_access(manifest, context)
        for manifest in sorted(CAPABILITY_MANIFESTS.values(), key=lambda manifest: manifest.id)
    ]
    return CurrentUserCapabilityContextResponse(
        current_organization=CurrentCapabilityOrganizationResponse(id=context.organization_id),
        organization_id=context.organization_id,
        user_id=context.user_id,
        installed_capability_ids=[
            installation.capability_id for installation in installations
        ],
        enabled_capability_ids=list(context.installed_capabilities),
        granted_permissions=list(context.granted_permissions),
        data_scopes=list(context.data_scopes),
        roles=list(context.roles),
        capability_decisions=[_access_decision_response(decision) for decision in decisions],
    )


@router.get("/manifest", response_model=CapabilityManifestListResponse)
async def list_capability_manifests(
    current_user: User = Depends(get_current_superuser),
) -> CapabilityManifestListResponse:
    """Return the canonical platform capability manifest registry."""

    _require_capability_admin(current_user)
    manifests = sorted(CAPABILITY_MANIFESTS.values(), key=lambda manifest: manifest.id)
    return CapabilityManifestListResponse(
        capabilities=[_manifest_response(manifest) for manifest in manifests],
    )


@router.get("/installations", response_model=CapabilityInstallationListResponse)
async def list_organization_capability_installations(
    organization_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CapabilityInstallationListResponse:
    """Return all persisted capability install rows for one organization."""

    _require_capability_admin(current_user)
    target_organization_id = _target_organization_id(current_user, organization_id)
    installations = await list_capability_installations(
        db,
        organization_id=target_organization_id,
    )
    return CapabilityInstallationListResponse(
        organization_id=target_organization_id,
        installations=[_installation_response(installation) for installation in installations],
    )


@router.post("/bootstrap", response_model=CapabilityBootstrapResponse)
async def bootstrap_first_wave_capabilities(
    payload: CapabilityBootstrapRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CapabilityBootstrapResponse:
    """Create missing first-wave install rows for one organization."""

    _require_capability_admin(current_user)
    payload = payload or CapabilityBootstrapRequest()
    target_organization_id = _target_organization_id(current_user, payload.organization_id)
    try:
        receipts = await bootstrap_capability_installations(
            db,
            organization_id=target_organization_id,
            actor_user_id=current_user.id,
            capability_ids=payload.capability_ids,
        )
    except UnknownCapability as exc:
        raise _unknown_capability(_unknown_capability_id_from_error(exc)) from exc

    return CapabilityBootstrapResponse(
        organization_id=target_organization_id,
        default_capability_ids=FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS,
        receipts=[_bootstrap_receipt_response(receipt) for receipt in receipts],
    )


@router.get("/{capability_id}", response_model=CapabilityStateResponse)
async def get_capability_state(
    capability_id: str,
    organization_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CapabilityStateResponse:
    """Return one capability manifest with this organization's install state."""

    _require_capability_admin(current_user)
    manifest = _resolve_manifest_or_404(capability_id)
    target_organization_id = _target_organization_id(current_user, organization_id)
    installation = await get_capability_installation(
        db,
        organization_id=target_organization_id,
        capability_id=capability_id,
    )
    return CapabilityStateResponse(
        manifest=_manifest_response(manifest),
        installation=_installation_response(installation) if installation else None,
    )


@router.put("/{capability_id}", response_model=CapabilityStateResponse)
async def install_capability(
    capability_id: str,
    payload: CapabilityInstallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CapabilityStateResponse:
    """Install or re-enable one capability for an organization."""

    _require_capability_admin(current_user)
    manifest = _resolve_manifest_or_404(capability_id)
    _validate_subset(
        payload.granted_permissions,
        allowed=manifest.required_permissions,
        field_name="granted_permissions",
    )
    _validate_subset(
        payload.data_scopes,
        allowed=manifest.data_scopes,
        field_name="data_scopes",
    )
    try:
        installation = await install_capability_for_organization(
            db,
            organization_id=_target_organization_id(current_user, payload.organization_id),
            capability_id=capability_id,
            actor_user_id=current_user.id,
            granted_permissions=payload.granted_permissions,
            data_scopes=payload.data_scopes,
            settings=payload.settings,
        )
    except UnknownCapability as exc:
        raise _unknown_capability(capability_id) from exc

    return CapabilityStateResponse(
        manifest=_manifest_response(manifest),
        installation=_installation_response(installation),
    )


@router.delete("/{capability_id}", response_model=CapabilityStateResponse)
async def disable_capability(
    capability_id: str,
    payload: CapabilityDisableRequest | None = None,
    organization_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CapabilityStateResponse:
    """Disable one organization's capability install without deleting data."""

    _require_capability_admin(current_user)
    manifest = _resolve_manifest_or_404(capability_id)
    request_organization_id = payload.organization_id if payload else organization_id
    try:
        installation = await disable_capability_for_organization(
            db,
            organization_id=_target_organization_id(current_user, request_organization_id),
            capability_id=capability_id,
            actor_user_id=current_user.id,
        )
    except UnknownCapability as exc:
        raise _unknown_capability(capability_id) from exc

    return CapabilityStateResponse(
        manifest=_manifest_response(manifest),
        installation=_installation_response(installation),
    )


def _require_capability_admin(current_user: User) -> None:
    if not bool(getattr(current_user, "is_superuser", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Capability management requires a superuser",
        )


def _target_organization_id(current_user: User, organization_id: int | None) -> int:
    if organization_id is not None:
        return organization_id
    return int(current_user.organization_id)


def _resolve_manifest_or_404(capability_id: str) -> CapabilityManifest:
    manifest = resolve_capability_manifest(capability_id)
    if manifest is None:
        raise _unknown_capability(capability_id)
    return manifest


def _unknown_capability(capability_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown capability '{capability_id}'",
    )


def _unknown_capability_id_from_error(error: UnknownCapability) -> str:
    message = str(error)
    if "'" in message:
        return message.split("'", 2)[1]
    return "unknown"


def _validate_subset(values: list[str] | None, *, allowed: tuple[str, ...], field_name: str) -> None:
    if values is None:
        return

    unknown = sorted(set(values) - set(allowed))
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "field": field_name,
                "unknown": unknown,
                "allowed": list(allowed),
            },
        )


def _manifest_response(manifest: CapabilityManifest) -> CapabilityManifestResponse:
    return CapabilityManifestResponse(
        id=manifest.id,
        title=manifest.title,
        dominion=manifest.dominion,
        owner_domain=manifest.owner_domain,
        supporting_domains=manifest.supporting_domains,
        lifecycle=manifest.lifecycle,
        standards=manifest.standards,
        frontend_routes=manifest.frontend_routes,
        backend_routes=manifest.backend_routes,
        data_scopes=manifest.data_scopes,
        required_permissions=manifest.required_permissions,
        suggested_roles=manifest.suggested_roles,
        semantic_spine_adrs=manifest.semantic_spine_adrs,
        install_behavior=manifest.install_behavior,
        uninstall_behavior=manifest.uninstall_behavior,
        tests=manifest.tests,
        audit_events=manifest.audit_events,
        source_context=manifest.source_context,
        backend_code_root=manifest.backend_code_root,
        frontend_code_root=manifest.frontend_code_root,
    )


def _bootstrap_receipt_response(
    receipt: CapabilityBootstrapReceipt,
) -> CapabilityBootstrapReceiptResponse:
    return CapabilityBootstrapReceiptResponse(
        capability_id=receipt.capability_id,
        organization_id=receipt.organization_id,
        action=receipt.action,
        enabled=receipt.enabled,
        lifecycle_state=receipt.lifecycle_state,
    )


def _installation_response(
    installation: OrganizationCapabilityInstallation,
) -> CapabilityInstallationResponse:
    return CapabilityInstallationResponse(
        capability_id=installation.capability_id,
        organization_id=installation.organization_id,
        enabled=installation.enabled,
        lifecycle_state=installation.lifecycle_state,
        granted_permissions=list(installation.granted_permissions or []),
        data_scopes=list(installation.data_scopes or []),
        settings=installation.settings,
        installed_by_user_id=installation.installed_by_user_id,
        disabled_by_user_id=installation.disabled_by_user_id,
        disabled_at=installation.disabled_at,
    )


def _access_decision_response(
    decision: CapabilityAccessDecision,
) -> CapabilityAccessDecisionResponse:
    return CapabilityAccessDecisionResponse(
        capability_id=decision.capability_id,
        allowed=decision.allowed,
        reason=decision.reason,
        missing_permissions=list(decision.missing_permissions),
        missing_data_scopes=list(decision.missing_data_scopes),
    )
