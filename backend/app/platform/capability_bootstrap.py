"""Explicit bootstrap helpers for first-wave platform capability installs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.capability_installations import (
    UnknownCapability,
    get_capability_installation,
    install_capability_for_organization,
)
from app.platform.dominions import resolve_capability_manifest


FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS = (
    "intelligence_fabric.knowledge_graph",
    "scientific_publishing_fair_exchange.research_asset_core",
)

CapabilityBootstrapAction = Literal[
    "installed",
    "already_installed",
    "skipped_disabled",
]


@dataclass(frozen=True)
class CapabilityBootstrapReceipt:
    """Primitive receipt for one capability bootstrap decision."""

    capability_id: str
    organization_id: int
    action: CapabilityBootstrapAction
    enabled: bool
    lifecycle_state: str


async def bootstrap_capability_installations(
    db: AsyncSession,
    *,
    organization_id: int,
    actor_user_id: int | None = None,
    capability_ids: Iterable[str] | None = None,
) -> list[CapabilityBootstrapReceipt]:
    """Install missing first-wave capability rows for one organization.

    Existing rows are treated as operator intent:
    - enabled rows are left unchanged
    - disabled rows stay disabled
    - absent rows are installed with manifest-default grants and scopes
    """

    resolved_capability_ids = _bootstrap_capability_ids(capability_ids)
    _validate_known_capabilities(resolved_capability_ids)

    receipts: list[CapabilityBootstrapReceipt] = []
    for capability_id in resolved_capability_ids:
        installation = await get_capability_installation(
            db,
            organization_id=organization_id,
            capability_id=capability_id,
        )
        if installation is None:
            installation = await install_capability_for_organization(
                db,
                organization_id=organization_id,
                capability_id=capability_id,
                actor_user_id=actor_user_id,
            )
            receipts.append(
                CapabilityBootstrapReceipt(
                    capability_id=capability_id,
                    organization_id=organization_id,
                    action="installed",
                    enabled=installation.enabled,
                    lifecycle_state=installation.lifecycle_state,
                )
            )
            continue

        action: CapabilityBootstrapAction = (
            "already_installed" if installation.enabled else "skipped_disabled"
        )
        receipts.append(
            CapabilityBootstrapReceipt(
                capability_id=capability_id,
                organization_id=organization_id,
                action=action,
                enabled=installation.enabled,
                lifecycle_state=installation.lifecycle_state,
            )
        )

    return receipts


def _bootstrap_capability_ids(capability_ids: Iterable[str] | None) -> tuple[str, ...]:
    if capability_ids is None:
        capability_ids = FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS
    return tuple(dict.fromkeys(str(capability_id) for capability_id in capability_ids))


def _validate_known_capabilities(capability_ids: tuple[str, ...]) -> None:
    for capability_id in capability_ids:
        if resolve_capability_manifest(capability_id) is None:
            raise UnknownCapability(f"Unknown capability '{capability_id}'")
