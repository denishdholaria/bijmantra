"""Infrastructure adapters for Intelligence Knowledge Graph use cases."""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph_persistence import (
    SqlAlchemyKnowledgeGraphPersistence,
)
from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphEvidencePackBuilder,
    KnowledgeGraphEvidenceSearchBuilder,
    KnowledgeGraphExplorerSnapshotBuilder,
    KnowledgeGraphRankedCandidatesBuilder,
    KnowledgeGraphReevuDryRunPreviewBuilder,
    KnowledgeGraphRetrievalCandidatesBuilder,
    KnowledgeGraphRetrievalDiagnosticsBuilder,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_edges import (
    deterministic_edge_id,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_vocabulary import (
    require_supported_direction,
    require_supported_relationship_type,
    require_supported_result_side,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphFairAssetRecord,
    KnowledgeGraphNeighborhoodRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphExplorerSnapshotQuery,
    KnowledgeGraphExplorerSnapshotResponse,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphFacetsQuery,
    KnowledgeGraphNeighborhoodQuery,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
    KnowledgeGraphRetrievalDiagnosticsQuery,
    KnowledgeGraphRetrievalDiagnosticsResponse,
    KnowledgeGraphUpsertEdgeCommand,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_fair_metadata_repository,
)
from app.domains.knowledge.capabilities.research_asset_core.application import (
    FairAssetMetadataApplicationService,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRepository,
)


FairMetadataRepositoryFactory = Callable[[AsyncSession], FairAssetMetadataRepository]


class SqlAlchemyKnowledgeGraphAdapter:
    """Adapter from Intelligence Knowledge Graph use case ports to SQLAlchemy persistence."""

    def __init__(
        self,
        db: AsyncSession,
        fair_metadata_service: FairAssetMetadataApplicationService | None = None,
        fair_metadata_repository_factory: FairMetadataRepositoryFactory | None = None,
    ) -> None:
        self._db = db
        self._fair_metadata_service = (
            fair_metadata_service or FairAssetMetadataApplicationService()
        )
        self._fair_metadata_repository_factory = (
            fair_metadata_repository_factory or build_fair_metadata_repository
        )

    def _persistence(self) -> SqlAlchemyKnowledgeGraphPersistence:
        return SqlAlchemyKnowledgeGraphPersistence(
            self._db,
            fair_metadata_repository=self._fair_metadata_repository_factory(self._db),
        )

    def normalize_result_side(self, result_side: str) -> str:
        return require_supported_result_side(result_side)

    def normalize_direction(self, direction: str) -> str:
        return require_supported_direction(direction)

    def normalize_asset_type(self, asset_type: str) -> str:
        return self._fair_metadata_service.require_supported_asset_type(asset_type)

    def normalize_relationship_type(self, relationship_type: str) -> str:
        return require_supported_relationship_type(relationship_type)

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRecord:
        metadata = await self._persistence().require_fair_asset(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_id,
        )
        return KnowledgeGraphFairAssetRecord(
            asset_type=asset_type,
            asset_id=asset_id,
            asset_title=metadata.title,
            persistent_identifier=metadata.persistent_identifier,
        )

    async def upsert_edge(
        self, command: KnowledgeGraphUpsertEdgeCommand
    ) -> KnowledgeGraphEdgeRecord:
        source_asset_type = self._fair_metadata_service.require_supported_asset_type(
            command.payload.source_asset_type
        )
        target_asset_type = self._fair_metadata_service.require_supported_asset_type(
            command.payload.target_asset_type
        )
        relationship_type = require_supported_relationship_type(
            command.payload.relationship_type
        )

        persistence = self._persistence()
        await persistence.require_fair_asset(
            organization_id=command.organization_id,
            asset_type=source_asset_type,
            asset_db_id=command.payload.source_asset_id,
        )
        await persistence.require_fair_asset(
            organization_id=command.organization_id,
            asset_type=target_asset_type,
            asset_db_id=command.payload.target_asset_id,
        )

        return await persistence.upsert_edge(
            organization_id=command.organization_id,
            payload=command.payload,
            source_asset_type=source_asset_type,
            target_asset_type=target_asset_type,
            relationship_type=relationship_type,
            edge_id=deterministic_edge_id(
                source_asset_type=source_asset_type,
                source_asset_id=command.payload.source_asset_id,
                relationship_type=relationship_type,
                target_asset_type=target_asset_type,
                target_asset_id=command.payload.target_asset_id,
            ),
        )

    async def build_explorer_snapshot(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        return await KnowledgeGraphExplorerSnapshotBuilder(self).execute(query)

    async def rank_retrieval_candidates(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        return await KnowledgeGraphRankedCandidatesBuilder(self).execute(query)

    async def build_retrieval_diagnostics(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        return await KnowledgeGraphRetrievalDiagnosticsBuilder(self).execute(query)

    async def build_retrieval_candidates(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        return await KnowledgeGraphRetrievalCandidatesBuilder(self).execute(query)

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        return await KnowledgeGraphEvidenceSearchBuilder(self).execute(query)

    async def get_facets(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        source_asset_type = (
            self._fair_metadata_service.require_supported_asset_type(
                query.source_asset_type
            )
            if query.source_asset_type
            else None
        )
        target_asset_type = (
            self._fair_metadata_service.require_supported_asset_type(
                query.target_asset_type
            )
            if query.target_asset_type
            else None
        )
        relationship_type = (
            require_supported_relationship_type(query.relationship_type)
            if query.relationship_type
            else None
        )
        persistence = self._persistence()
        total_edge_count = await persistence.count_edges(
            organization_id=query.organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=relationship_type,
        )
        return KnowledgeGraphFacetResponse(
            source_asset_type=source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=relationship_type,
            total_edge_count=total_edge_count,
            relationship_type_counts=await persistence.count_by_edge_column(
                column_name="relationship_type",
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            source_asset_type_counts=await persistence.count_by_edge_column(
                column_name="source_asset_type",
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            target_asset_type_counts=await persistence.count_by_edge_column(
                column_name="target_asset_type",
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            status_counts=await persistence.count_by_edge_column(
                column_name="status",
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            derivation_method_counts=await persistence.count_by_edge_column(
                column_name="derivation_method",
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            asset_type_pair_counts=await persistence.count_asset_type_pairs(
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
            ),
            retrieval_policy={
                "graphDepth": 1,
                "facetOnly": True,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
        )

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeRecord]:
        source_asset_type = (
            self._fair_metadata_service.require_supported_asset_type(
                query.source_asset_type
            )
            if query.source_asset_type
            else None
        )
        target_asset_type = (
            self._fair_metadata_service.require_supported_asset_type(
                query.target_asset_type
            )
            if query.target_asset_type
            else None
        )
        relationship_type = (
            require_supported_relationship_type(query.relationship_type)
            if query.relationship_type
            else None
        )
        return await self._persistence().list_edges(
            organization_id=query.organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=relationship_type,
            limit=query.limit,
            offset=query.offset,
        )

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodRecord:
        asset_type = self._fair_metadata_service.require_supported_asset_type(
            query.asset_type
        )
        direction = require_supported_direction(query.direction)
        relationship_type = (
            require_supported_relationship_type(query.relationship_type)
            if query.relationship_type
            else None
        )
        persistence = self._persistence()
        await persistence.require_fair_asset(
            organization_id=query.organization_id,
            asset_type=asset_type,
            asset_db_id=query.asset_id,
        )

        outgoing_edges: list[KnowledgeGraphEdgeRecord] = []
        incoming_edges: list[KnowledgeGraphEdgeRecord] = []
        if direction in {"outgoing", "both"}:
            outgoing_edges = await persistence.list_neighborhood_edges(
                organization_id=query.organization_id,
                asset_type=asset_type,
                asset_id=query.asset_id,
                relationship_type=relationship_type,
                incoming=False,
                limit=query.limit,
                offset=query.offset,
            )
        if direction in {"incoming", "both"}:
            incoming_edges = await persistence.list_neighborhood_edges(
                organization_id=query.organization_id,
                asset_type=asset_type,
                asset_id=query.asset_id,
                relationship_type=relationship_type,
                incoming=True,
                limit=query.limit,
                offset=query.offset,
            )

        return KnowledgeGraphNeighborhoodRecord(
            asset_type=asset_type,
            asset_id=query.asset_id,
            direction=direction,
            relationship_type=relationship_type,
            outgoing_edges=outgoing_edges,
            incoming_edges=incoming_edges,
            edge_count=len(outgoing_edges) + len(incoming_edges),
        )

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        return await KnowledgeGraphEvidencePackBuilder(self).execute(query)

    async def build_reevu_dry_run_preview(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        return await KnowledgeGraphReevuDryRunPreviewBuilder(self).execute(query)


class SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter(SqlAlchemyKnowledgeGraphAdapter):
    """Backward-compatible alias for the first Intelligence Knowledge Graph bridge."""
