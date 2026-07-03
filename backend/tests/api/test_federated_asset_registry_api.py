from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.federated_assets import (
    create_federated_connector,
    list_federated_asset_audit_events,
    list_federated_assets,
    list_federated_connectors,
    list_federated_sync_receipts,
    promote_federated_asset_to_fair_metadata,
    register_federated_asset,
    run_federated_connector_dry_run,
)
from app.domains.knowledge.capabilities.research_asset_core.domain import (
    FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
    FEDERATED_ASSET_REGISTER_ACTION,
    FEDERATED_CONNECTOR_DRY_RUN_ACTION,
    FEDERATED_CONNECTOR_UPSERT_ACTION,
)
from app.models.audit import AuditLog
from app.models.fair_metadata import FairAssetMetadata
from app.models.federated_assets import (
    FederatedAssetConnector,
    FederatedAssetRecord,
    FederatedAssetSyncReceipt,
)
from app.schemas.federated_assets import (
    FederatedAssetFairPromotionRequest,
    FederatedAssetConnectorCreate,
    FederatedAssetDryRunRequest,
    FederatedAssetRegistrationCreate,
)


@pytest.fixture(autouse=True)
async def create_federated_asset_api_tables(async_db_session: AsyncSession):
    engine = async_db_session.bind
    tables = [
        AuditLog.__table__,
        FairAssetMetadata.__table__,
        FederatedAssetConnector.__table__,
        FederatedAssetRecord.__table__,
        FederatedAssetSyncReceipt.__table__,
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(lambda sync_conn, table=table: table.create(sync_conn, checkfirst=True))
    yield


def _current_user(test_user):
    return SimpleNamespace(id=test_user.id, organization_id=test_user.organization_id)


def _connector_payload() -> FederatedAssetConnectorCreate:
    return FederatedAssetConnectorCreate(
        connector_key=f"api-brapi-{uuid4().hex[:8]}",
        connector_type="brapi_server",
        display_name="API BrAPI connector",
        endpoint_url="https://example.org/brapi/v2",
        capabilities=["germplasm"],
        standards=["BrAPI v2.1"],
    )


@pytest.mark.asyncio
async def test_federated_assets_api_connector_dry_run_register_and_list_shape(
    async_db_session: AsyncSession,
    test_user,
):
    current_user = _current_user(test_user)
    created_connector = await create_federated_connector(
        payload=_connector_payload(),
        db=async_db_session,
        current_user=current_user,
    )

    assert created_connector.organization_id == test_user.organization_id
    assert created_connector.connector_type == "brapi_server"

    connectors = await list_federated_connectors(
        db=async_db_session,
        current_user=current_user,
    )
    assert any(connector.id == created_connector.id for connector in connectors)

    receipt = await run_federated_connector_dry_run(
        connector_key=created_connector.connector_key,
        payload=FederatedAssetDryRunRequest(
            candidate_assets=[
                {
                    "externalAssetId": "dataset:api-rice-yield",
                    "assetKind": "dataset",
                    "title": "API Rice Yield Dataset",
                }
            ]
        ),
        db=async_db_session,
        current_user=current_user,
    )
    assert receipt.run_mode == "dry_run"
    assert receipt.registered_asset_count == 0
    assert receipt.discovered_asset_count == 1
    assert receipt.schema_version == "federated_sync_receipt.v1"

    asset = await register_federated_asset(
        payload=FederatedAssetRegistrationCreate(
            connector_key=created_connector.connector_key,
            external_asset_id="dataset:api-rice-yield",
            asset_kind="dataset",
            title="API Rice Yield Dataset",
            data_standard="BrAPI v2.1",
        ),
        db=async_db_session,
        current_user=current_user,
    )
    assert asset.registry_asset_id.startswith("fedasset-")
    assert asset.title == "API Rice Yield Dataset"

    promoted_asset = await promote_federated_asset_to_fair_metadata(
        registry_asset_id=asset.registry_asset_id,
        payload=FederatedAssetFairPromotionRequest(keywords=["api", "fair"]),
        db=async_db_session,
        current_user=current_user,
    )
    assert promoted_asset.fair_metadata_id is not None

    audit_events = await list_federated_asset_audit_events(
        target_type=None,
        target_id=None,
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )
    assert [event.action for event in audit_events] == [
        FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
        FEDERATED_ASSET_REGISTER_ACTION,
        FEDERATED_CONNECTOR_DRY_RUN_ACTION,
        FEDERATED_CONNECTOR_UPSERT_ACTION,
    ]
    assert audit_events[0].organization_id == test_user.organization_id
    assert audit_events[0].user_id == test_user.id

    assets = await list_federated_assets(
        connector_key=created_connector.connector_key,
        asset_kind="dataset",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )
    assert [item.id for item in assets] == [asset.id]

    receipts = await list_federated_sync_receipts(
        connector_key=created_connector.connector_key,
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=current_user,
    )
    assert [item.id for item in receipts] == [receipt.id]
