import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph_persistence import (
    SqlAlchemyKnowledgeGraphPersistence,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    GraphAssetNotFound,
    KnowledgeGraphEdgeCreate,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_fair_metadata_repository,
)
from app.models.fair_metadata import FairAssetMetadata
from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge


@pytest.fixture(autouse=True)
async def create_knowledge_graph_persistence_tables(async_db_session: AsyncSession):
    engine = async_db_session.bind
    tables = [
        FairAssetMetadata.__table__,
        AgriculturalKnowledgeGraphEdge.__table__,
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(
                lambda sync_conn, table=table: table.create(sync_conn, checkfirst=True)
            )
    yield


async def _fair_asset(
    db: AsyncSession,
    *,
    organization_id: int,
    asset_type: str,
    asset_db_id: str,
    title: str,
) -> None:
    db.add(
        FairAssetMetadata(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            persistent_identifier=f"bijmantra:{asset_type}:{asset_db_id}",
            title=title,
            schema_version="fair_asset_metadata.v1",
        )
    )
    await db.flush()


def _persistence(db: AsyncSession) -> SqlAlchemyKnowledgeGraphPersistence:
    return SqlAlchemyKnowledgeGraphPersistence(
        db,
        fair_metadata_repository=build_fair_metadata_repository(db),
    )


@pytest.mark.asyncio
async def test_intelligence_persistence_adapter_upserts_and_lists_edges(
    async_db_session: AsyncSession,
) -> None:
    await _fair_asset(
        async_db_session,
        organization_id=7,
        asset_type="germplasm",
        asset_db_id="IR64",
        title="IR64",
    )
    await _fair_asset(
        async_db_session,
        organization_id=7,
        asset_type="observation_variable",
        asset_db_id="CO:0000001",
        title="Drought tolerance",
    )
    persistence = _persistence(async_db_session)

    edge = await persistence.upsert_edge(
        organization_id=7,
        payload=KnowledgeGraphEdgeCreate(
            source_asset_type="germplasm",
            source_asset_id="IR64",
            relationship_type="has_trait",
            target_asset_type="observation_variable",
            target_asset_id="CO:0000001",
            evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
            confidence=0.88,
            derivation_method="manual_curated",
        ),
        source_asset_type="germplasm",
        target_asset_type="observation_variable",
        relationship_type="has_trait",
        edge_id="kg-edge-test",
    )

    assert isinstance(edge, KnowledgeGraphEdgeRecord)
    assert edge.edge_id == "kg-edge-test"

    listed = await persistence.list_edges(
        organization_id=7,
        source_asset_type="germplasm",
        source_asset_id="IR64",
        target_asset_type=None,
        target_asset_id=None,
        relationship_type="has_trait",
    )

    assert all(isinstance(item, KnowledgeGraphEdgeRecord) for item in listed)
    assert [item.id for item in listed] == [edge.id]
    assert await persistence.count_edges(
        organization_id=7,
        source_asset_type="germplasm",
        source_asset_id=None,
        target_asset_type=None,
        target_asset_id=None,
        relationship_type=None,
    ) == 1
    assert await persistence.count_by_edge_column(
        column_name="relationship_type",
        organization_id=7,
        source_asset_type=None,
        source_asset_id=None,
        target_asset_type=None,
        target_asset_id=None,
        relationship_type=None,
    ) == {"has_trait": 1}
    assert [pair.model_dump() for pair in await persistence.count_asset_type_pairs(
        organization_id=7,
        source_asset_type=None,
        source_asset_id=None,
        target_asset_type=None,
        target_asset_id=None,
        relationship_type=None,
    )] == [
        {
            "source_asset_type": "germplasm",
            "target_asset_type": "observation_variable",
            "count": 1,
        }
    ]


@pytest.mark.asyncio
async def test_intelligence_persistence_adapter_raises_for_missing_fair_asset(
    async_db_session: AsyncSession,
) -> None:
    persistence = _persistence(async_db_session)

    with pytest.raises(GraphAssetNotFound):
        await persistence.require_fair_asset(
            organization_id=7,
            asset_type="germplasm",
            asset_db_id="MISSING",
        )
