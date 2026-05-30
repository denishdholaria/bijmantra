from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.fair_metadata import (
    list_fair_metadata,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.api.federated_assets import (
    promote_federated_asset_to_fair_metadata,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.federated_assets import (
    FederatedAssetFairPromotionRequest,
)


RESEARCH_ASSET_CAPABILITY_ID = "scientific_publishing_fair_exchange.research_asset_core"


def _actor(
    *,
    installed_capabilities: tuple[str, ...] = (RESEARCH_ASSET_CAPABILITY_ID,),
    permissions: tuple[str, ...] = (
        "research_assets.read",
        "research_assets.register",
        "research_assets.promote_fair",
    ),
    data_scopes: tuple[str, ...] = (
        "organization",
        "asset",
        "provenance",
        "license",
        "identifier",
        "connector",
        "evidence",
    ),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=42,
        organization_id=7,
        installed_capabilities=installed_capabilities,
        permissions=permissions,
        data_scopes=data_scopes,
        roles=("data_steward",),
    )


@pytest.mark.asyncio
async def test_research_asset_api_rejects_uninstalled_capability_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await list_fair_metadata(
            asset_type=None,
            limit=20,
            offset=0,
            db=object(),
            current_user=_actor(installed_capabilities=()),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"
    assert error.value.detail["capabilityId"] == RESEARCH_ASSET_CAPABILITY_ID


@pytest.mark.asyncio
async def test_research_asset_api_rejects_missing_permission_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await promote_federated_asset_to_fair_metadata(
            registry_asset_id="fedasset-test",
            payload=FederatedAssetFairPromotionRequest(),
            db=object(),
            current_user=_actor(permissions=("research_assets.read",)),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_permission"
    assert error.value.detail["missingPermissions"] == ["research_assets.promote_fair"]


@pytest.mark.asyncio
async def test_research_asset_api_rejects_missing_data_scope_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await promote_federated_asset_to_fair_metadata(
            registry_asset_id="fedasset-test",
            payload=FederatedAssetFairPromotionRequest(),
            db=object(),
            current_user=_actor(data_scopes=("organization", "asset")),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_data_scope"
    assert error.value.detail["missingDataScopes"] == ["provenance", "identifier"]
