import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.capabilities.research_asset_core.domain import (
    FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
    FEDERATED_ASSET_REGISTER_ACTION,
    FEDERATED_CONNECTOR_DRY_RUN_ACTION,
    FEDERATED_CONNECTOR_UPSERT_ACTION,
)
from app.models.audit import AuditLog
from app.models.core import Organization
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
from app.services.federated_asset_registry_service import (
    FederatedAssetNotFound,
    FederatedAssetRegistryService,
    FederatedConnectorNotFound,
    UnsupportedFederatedAssetKind,
    UnsupportedFederatedConnectorType,
)


@pytest.fixture(autouse=True)
async def create_federated_asset_tables(async_db_session: AsyncSession):
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


def _suffix() -> str:
    return uuid.uuid4().hex[:8]


def _connector_payload(connector_key: str | None = None) -> FederatedAssetConnectorCreate:
    suffix = _suffix()
    return FederatedAssetConnectorCreate(
        connector_key=connector_key or f"irri-brapi-{suffix}",
        connector_type="brapi_server",
        display_name="IRRI BrAPI metadata catalog",
        endpoint_url="https://example.org/brapi/v2",
        capabilities=["germplasm", "studies", "trials"],
        standards=["BrAPI v2.1", "MCPD"],
        governance={"license_review_required": True},
    )


def _candidate_assets() -> list[dict]:
    return [
        {
            "externalAssetId": "dataset:rice-yield-2026",
            "assetKind": "dataset",
            "title": "Rice Yield Trial Metadata 2026",
            "sourceUri": "https://example.org/datasets/rice-yield-2026",
            "license": "CC-BY-4.0",
            "dataStandard": "BrAPI v2.1",
        }
    ]


async def _other_org(db: AsyncSession) -> Organization:
    org = Organization(name=f"Federated Other Org {_suffix()}")
    db.add(org)
    await db.flush()
    return org


@pytest.mark.asyncio
async def test_dry_run_writes_receipt_but_no_registry_asset_rows(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )

    receipt = await service.run_connector_dry_run(
        async_db_session,
        organization_id=test_user.organization_id,
        connector_key=connector.connector_key,
        payload=FederatedAssetDryRunRequest(candidate_assets=_candidate_assets()),
    )

    assert receipt.organization_id == test_user.organization_id
    assert receipt.connector_id == connector.id
    assert receipt.run_mode == "dry_run"
    assert receipt.status == "dry_run_completed"
    assert receipt.discovered_asset_count == 1
    assert receipt.registered_asset_count == 0
    assert receipt.skipped_asset_count == 1
    assert receipt.source_digest
    assert receipt.manifest_snapshot["connector"]["connectorKey"] == connector.connector_key

    records = await async_db_session.scalars(select(FederatedAssetRecord))
    assert list(records) == []


@pytest.mark.asyncio
async def test_explicit_registration_creates_metadata_only_asset_record(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )

    asset = await service.register_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=FederatedAssetRegistrationCreate(
            connector_key=connector.connector_key,
            external_asset_id="dataset:rice-yield-2026",
            asset_kind="dataset",
            title="Rice Yield Trial Metadata 2026",
            source_uri="https://example.org/datasets/rice-yield-2026",
            license="CC-BY-4.0",
            data_standard="BrAPI v2.1",
            standards_mappings={"brapi": "v2.1"},
            metadata={"crop": "rice"},
            provenance={"registered_from": "operator-reviewed dry run"},
        ),
    )

    assert asset.organization_id == test_user.organization_id
    assert asset.connector_id == connector.id
    assert asset.registry_asset_id.startswith("fedasset-")
    assert asset.asset_kind == "dataset"
    assert asset.source_digest
    assert asset.asset_metadata == {"crop": "rice"}


@pytest.mark.asyncio
async def test_promote_asset_to_fair_metadata_creates_sidecar_and_links_registry_asset(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )
    asset = await service.register_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=FederatedAssetRegistrationCreate(
            connector_key=connector.connector_key,
            external_asset_id="dataset:rice-yield-2026",
            asset_kind="dataset",
            title="Rice Yield Trial Metadata 2026",
            description="Reviewed public metadata for rice yield trials.",
            source_uri="https://example.org/datasets/rice-yield-2026",
            license="CC-BY-4.0",
            data_standard="BrAPI v2.1",
            provenance={"registered_from": "operator-reviewed dry run"},
        ),
    )

    promoted = await service.promote_asset_to_fair_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        registry_asset_id=asset.registry_asset_id,
        payload=FederatedAssetFairPromotionRequest(
            access_rights="open",
            keywords=["rice", "yield"],
            ontology_terms=["CO:0000001"],
            confidence=0.91,
        ),
    )

    assert promoted.fair_metadata_id is not None
    metadata = await async_db_session.get(FairAssetMetadata, promoted.fair_metadata_id)
    assert metadata is not None
    assert metadata.organization_id == test_user.organization_id
    assert metadata.asset_type == "federated_asset"
    assert metadata.asset_db_id == asset.registry_asset_id
    assert metadata.persistent_identifier == f"bijmantra:federated_asset:{asset.registry_asset_id}"
    assert metadata.title == "Rice Yield Trial Metadata 2026"
    assert metadata.description == "Reviewed public metadata for rice yield trials."
    assert metadata.license == "CC-BY-4.0"
    assert metadata.data_standard == "BrAPI v2.1"
    assert metadata.keywords == ["rice", "yield"]
    assert metadata.ontology_terms == ["CO:0000001"]
    assert metadata.provenance["promotion"]["workflow"] == "federated_asset_fair_promotion.v1"
    assert metadata.provenance["sourceProvenance"] == {
        "registered_from": "operator-reviewed dry run"
    }
    assert metadata.external_references[0]["registryAssetId"] == asset.registry_asset_id
    assert metadata.external_references[0]["connectorKey"] == connector.connector_key


@pytest.mark.asyncio
async def test_promote_asset_to_fair_metadata_reuses_existing_sidecar(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )
    asset = await service.register_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=FederatedAssetRegistrationCreate(
            connector_key=connector.connector_key,
            external_asset_id="dataset:rice-yield-idempotent",
            asset_kind="dataset",
            title="Rice Yield Idempotent Dataset",
        ),
    )

    first = await service.promote_asset_to_fair_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        registry_asset_id=asset.registry_asset_id,
        payload=FederatedAssetFairPromotionRequest(keywords=["first"]),
    )
    second = await service.promote_asset_to_fair_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        registry_asset_id=asset.registry_asset_id,
        payload=FederatedAssetFairPromotionRequest(keywords=["second"]),
    )

    assert second.fair_metadata_id == first.fair_metadata_id
    result = await async_db_session.scalars(
        select(FairAssetMetadata).where(
            FairAssetMetadata.organization_id == test_user.organization_id,
            FairAssetMetadata.asset_type == "federated_asset",
            FairAssetMetadata.asset_db_id == asset.registry_asset_id,
        )
    )
    records = list(result)
    assert len(records) == 1
    assert records[0].keywords == ["second"]


@pytest.mark.asyncio
async def test_promote_asset_to_fair_metadata_rejects_cross_tenant_registry_asset(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )
    asset = await service.register_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=FederatedAssetRegistrationCreate(
            connector_key=connector.connector_key,
            external_asset_id="dataset:tenant-boundary",
            asset_kind="dataset",
            title="Tenant Boundary Dataset",
        ),
    )
    other = await _other_org(async_db_session)

    with pytest.raises(FederatedAssetNotFound):
        await service.promote_asset_to_fair_metadata(
            async_db_session,
            organization_id=other.id,
            registry_asset_id=asset.registry_asset_id,
            payload=FederatedAssetFairPromotionRequest(),
        )


@pytest.mark.asyncio
async def test_federated_registry_writes_canonical_audit_events_for_mutations(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    actor_user_id = test_user.id
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        actor_user_id=actor_user_id,
        payload=_connector_payload(),
    )
    await service.run_connector_dry_run(
        async_db_session,
        organization_id=test_user.organization_id,
        actor_user_id=actor_user_id,
        connector_key=connector.connector_key,
        payload=FederatedAssetDryRunRequest(candidate_assets=_candidate_assets()),
    )
    asset = await service.register_asset(
        async_db_session,
        organization_id=test_user.organization_id,
        actor_user_id=actor_user_id,
        payload=FederatedAssetRegistrationCreate(
            connector_key=connector.connector_key,
            external_asset_id="dataset:audit-rice-yield",
            asset_kind="dataset",
            title="Audit Rice Yield Dataset",
        ),
    )
    await service.promote_asset_to_fair_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        actor_user_id=actor_user_id,
        registry_asset_id=asset.registry_asset_id,
        payload=FederatedAssetFairPromotionRequest(keywords=["audit"]),
    )

    events = await service.list_audit_events(
        async_db_session,
        organization_id=test_user.organization_id,
        limit=20,
        offset=0,
    )

    assert [event.action for event in events] == [
        FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
        FEDERATED_ASSET_REGISTER_ACTION,
        FEDERATED_CONNECTOR_DRY_RUN_ACTION,
        FEDERATED_CONNECTOR_UPSERT_ACTION,
    ]
    assert {event.organization_id for event in events} == {test_user.organization_id}
    assert {event.user_id for event in events} == {actor_user_id}
    assert events[0].target_type == "federated_asset_record"
    assert events[0].target_id == asset.registry_asset_id
    assert events[0].changes["fairMetadataId"] is not None
    assert events[2].changes["receiptId"].startswith("fed-sync-")


@pytest.mark.asyncio
async def test_federated_registry_audit_listing_is_tenant_scoped(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )
    other = await _other_org(async_db_session)

    other_events = await service.list_audit_events(
        async_db_session,
        organization_id=other.id,
        limit=20,
        offset=0,
    )

    assert connector.organization_id == test_user.organization_id
    assert other_events == []


@pytest.mark.asyncio
async def test_federated_registry_enforces_tenant_scoped_connectors(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(connector_key=f"tenant-brapi-{_suffix()}"),
    )
    other = await _other_org(async_db_session)

    assert (
        await service.get_connector(
            async_db_session,
            organization_id=other.id,
            connector_key=connector.connector_key,
        )
        is None
    )
    with pytest.raises(FederatedConnectorNotFound):
        await service.run_connector_dry_run(
            async_db_session,
            organization_id=other.id,
            connector_key=connector.connector_key,
            payload=FederatedAssetDryRunRequest(candidate_assets=_candidate_assets()),
        )


@pytest.mark.asyncio
async def test_federated_registry_rejects_unsupported_connector_and_asset_kind(
    async_db_session: AsyncSession,
    test_user,
):
    service = FederatedAssetRegistryService()
    with pytest.raises(UnsupportedFederatedConnectorType):
        await service.create_connector(
            async_db_session,
            organization_id=test_user.organization_id,
            payload=FederatedAssetConnectorCreate(
                connector_key=f"bad-{_suffix()}",
                connector_type="spreadsheet_scraper",
                display_name="Unsupported",
            ),
        )

    connector = await service.create_connector(
        async_db_session,
        organization_id=test_user.organization_id,
        payload=_connector_payload(),
    )
    with pytest.raises(UnsupportedFederatedAssetKind):
        await service.register_asset(
            async_db_session,
            organization_id=test_user.organization_id,
            payload=FederatedAssetRegistrationCreate(
                connector_key=connector.connector_key,
                external_asset_id="legacy-report-1",
                asset_kind="raw_report",
                title="Legacy report",
            ),
        )
