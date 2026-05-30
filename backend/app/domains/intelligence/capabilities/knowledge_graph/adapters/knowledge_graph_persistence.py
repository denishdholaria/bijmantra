"""SQLAlchemy persistence adapter for Intelligence Knowledge Graph data."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    GraphAssetNotFound,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRecord,
    FairAssetMetadataRepository,
)
from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge
from app.schemas.knowledge_graph import (
    KnowledgeGraphAssetTypePairFacet,
    KnowledgeGraphEdgeCreate,
)


class SqlAlchemyKnowledgeGraphPersistence:
    """Tenant-scoped Knowledge Graph persistence operations."""

    _COUNT_COLUMNS = {
        "relationship_type": AgriculturalKnowledgeGraphEdge.relationship_type,
        "source_asset_type": AgriculturalKnowledgeGraphEdge.source_asset_type,
        "target_asset_type": AgriculturalKnowledgeGraphEdge.target_asset_type,
        "status": AgriculturalKnowledgeGraphEdge.status,
        "derivation_method": AgriculturalKnowledgeGraphEdge.derivation_method,
    }

    def __init__(
        self,
        db: AsyncSession,
        *,
        fair_metadata_repository: FairAssetMetadataRepository,
    ) -> None:
        self._db = db
        self._fair_metadata_repository = fair_metadata_repository

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord:
        metadata = await self._fair_metadata_repository.get_metadata(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )
        if metadata is None:
            raise GraphAssetNotFound(
                f"FAIR asset '{asset_type}:{asset_db_id}' was not found in this organization"
            )
        return metadata

    async def upsert_edge(
        self,
        *,
        organization_id: int,
        payload: KnowledgeGraphEdgeCreate,
        source_asset_type: str,
        target_asset_type: str,
        relationship_type: str,
        edge_id: str,
    ) -> AgriculturalKnowledgeGraphEdge:
        result = await self._db.execute(
            select(AgriculturalKnowledgeGraphEdge).where(
                AgriculturalKnowledgeGraphEdge.organization_id == organization_id,
                AgriculturalKnowledgeGraphEdge.source_asset_type == source_asset_type,
                AgriculturalKnowledgeGraphEdge.source_asset_id == payload.source_asset_id,
                AgriculturalKnowledgeGraphEdge.relationship_type == relationship_type,
                AgriculturalKnowledgeGraphEdge.target_asset_type == target_asset_type,
                AgriculturalKnowledgeGraphEdge.target_asset_id == payload.target_asset_id,
            )
        )
        edge = result.scalar_one_or_none()
        if edge is None:
            edge = AgriculturalKnowledgeGraphEdge(
                organization_id=organization_id,
                edge_id=edge_id,
                source_asset_type=source_asset_type,
                source_asset_id=payload.source_asset_id,
                relationship_type=relationship_type,
                target_asset_type=target_asset_type,
                target_asset_id=payload.target_asset_id,
            )
            self._db.add(edge)

        edge.evidence_refs = list(payload.evidence_refs or [])
        edge.provenance = dict(payload.provenance or {})
        edge.confidence = payload.confidence
        edge.derivation_method = payload.derivation_method
        edge.status = payload.status or "active"
        edge.schema_version = edge.schema_version or "agricultural_knowledge_graph_edge.v1"

        await self._db.flush()
        await self._db.refresh(edge)
        return edge

    async def list_edges(
        self,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgriculturalKnowledgeGraphEdge]:
        stmt = select(AgriculturalKnowledgeGraphEdge).where(
            *self._edge_filter_conditions(
                organization_id=organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=target_asset_id,
                relationship_type=relationship_type,
            )
        )
        stmt = (
            stmt.order_by(AgriculturalKnowledgeGraphEdge.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_neighborhood_edges(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
        relationship_type: str | None,
        incoming: bool,
        limit: int,
        offset: int,
    ) -> list[AgriculturalKnowledgeGraphEdge]:
        stmt = select(AgriculturalKnowledgeGraphEdge).where(
            AgriculturalKnowledgeGraphEdge.organization_id == organization_id
        )
        if incoming:
            stmt = stmt.where(
                AgriculturalKnowledgeGraphEdge.target_asset_type == asset_type,
                AgriculturalKnowledgeGraphEdge.target_asset_id == asset_id,
            )
        else:
            stmt = stmt.where(
                AgriculturalKnowledgeGraphEdge.source_asset_type == asset_type,
                AgriculturalKnowledgeGraphEdge.source_asset_id == asset_id,
            )
        if relationship_type:
            stmt = stmt.where(AgriculturalKnowledgeGraphEdge.relationship_type == relationship_type)
        stmt = (
            stmt.order_by(AgriculturalKnowledgeGraphEdge.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_edges(
        self,
        *,
        organization_id: int,
        source_asset_type: str | None,
        source_asset_id: str | None,
        target_asset_type: str | None,
        target_asset_id: str | None,
        relationship_type: str | None,
    ) -> int:
        filters = self._edge_filter_conditions(
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
        )
        result = await self._db.execute(
            select(func.count(AgriculturalKnowledgeGraphEdge.id)).where(*filters)
        )
        return int(result.scalar_one())

    async def count_by_edge_column(
        self,
        *,
        column_name: str,
        organization_id: int,
        source_asset_type: str | None,
        source_asset_id: str | None,
        target_asset_type: str | None,
        target_asset_id: str | None,
        relationship_type: str | None,
    ) -> dict[str, int]:
        column = self._COUNT_COLUMNS[column_name]
        filters = self._edge_filter_conditions(
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
        )
        result = await self._db.execute(
            select(column, func.count(AgriculturalKnowledgeGraphEdge.id))
            .where(*filters)
            .where(column.is_not(None))
            .group_by(column)
            .order_by(column)
        )
        return {str(value): int(count) for value, count in result.all()}

    async def count_asset_type_pairs(
        self,
        *,
        organization_id: int,
        source_asset_type: str | None,
        source_asset_id: str | None,
        target_asset_type: str | None,
        target_asset_id: str | None,
        relationship_type: str | None,
    ) -> list[KnowledgeGraphAssetTypePairFacet]:
        filters = self._edge_filter_conditions(
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
        )
        result = await self._db.execute(
            select(
                AgriculturalKnowledgeGraphEdge.source_asset_type,
                AgriculturalKnowledgeGraphEdge.target_asset_type,
                func.count(AgriculturalKnowledgeGraphEdge.id),
            )
            .where(*filters)
            .group_by(
                AgriculturalKnowledgeGraphEdge.source_asset_type,
                AgriculturalKnowledgeGraphEdge.target_asset_type,
            )
            .order_by(
                AgriculturalKnowledgeGraphEdge.source_asset_type,
                AgriculturalKnowledgeGraphEdge.target_asset_type,
            )
        )
        return [
            KnowledgeGraphAssetTypePairFacet(
                source_asset_type=source_asset_type,
                target_asset_type=target_asset_type,
                count=int(count),
            )
            for source_asset_type, target_asset_type, count in result.all()
        ]

    def _edge_filter_conditions(
        self,
        *,
        organization_id: int,
        source_asset_type: str | None,
        source_asset_id: str | None,
        target_asset_type: str | None,
        target_asset_id: str | None,
        relationship_type: str | None,
    ) -> list[Any]:
        filters: list[Any] = [
            AgriculturalKnowledgeGraphEdge.organization_id == organization_id,
        ]
        if source_asset_type:
            filters.append(AgriculturalKnowledgeGraphEdge.source_asset_type == source_asset_type)
        if source_asset_id:
            filters.append(AgriculturalKnowledgeGraphEdge.source_asset_id == source_asset_id)
        if target_asset_type:
            filters.append(AgriculturalKnowledgeGraphEdge.target_asset_type == target_asset_type)
        if target_asset_id:
            filters.append(AgriculturalKnowledgeGraphEdge.target_asset_id == target_asset_id)
        if relationship_type:
            filters.append(AgriculturalKnowledgeGraphEdge.relationship_type == relationship_type)
        return filters
