"""Tenant-scoped agricultural knowledge graph edge service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph import (
    SqlAlchemyKnowledgeGraphAdapter,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_vocabulary import (
    normalize_relationship_type as normalize_graph_relationship_type,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_vocabulary import (
    require_supported_direction as require_graph_direction,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_vocabulary import (
    require_supported_relationship_type as require_graph_relationship_type,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_vocabulary import (
    require_supported_result_side as require_graph_result_side,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    GraphAssetNotFound as GraphAssetNotFound,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeCreate,
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
    KnowledgeGraphNeighborhoodResponse,
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
    FairAssetMetadataRecord,
    FairAssetMetadataRepository,
)


class UnsupportedGraphRelationshipType(ValueError):
    """Raised when a graph relationship is outside the first supported vocabulary."""


class UnsupportedGraphDirection(ValueError):
    """Raised when a neighborhood direction is outside the supported one-hop modes."""


class UnsupportedGraphResultSide(ValueError):
    """Raised when evidence search asks for an unsupported result projection side."""


class KnowledgeGraphService:
    """Create and query evidence-carrying graph edges over FAIR assets."""

    def __init__(
        self,
        fair_metadata_service: FairAssetMetadataApplicationService | None = None,
        fair_metadata_repository_factory: Any | None = None,
    ) -> None:
        self.fair_metadata_service = (
            fair_metadata_service or FairAssetMetadataApplicationService()
        )
        self._fair_metadata_repository_factory = (
            fair_metadata_repository_factory or build_fair_metadata_repository
        )

    def _adapter(self, db: AsyncSession) -> SqlAlchemyKnowledgeGraphAdapter:
        return SqlAlchemyKnowledgeGraphAdapter(
            db,
            fair_metadata_service=self.fair_metadata_service,
            fair_metadata_repository_factory=self._fair_metadata_repository_factory,
        )

    def _fair_metadata_repository(self, db: AsyncSession) -> FairAssetMetadataRepository:
        return self._fair_metadata_repository_factory(db)

    async def require_fair_asset(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord:
        metadata = await self._fair_metadata_repository(db).get_metadata(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )
        if metadata is None:
            raise GraphAssetNotFound(
                f"FAIR asset '{asset_type}:{asset_db_id}' was not found in this organization"
            )
        return metadata

    def normalize_relationship_type(self, relationship_type: str) -> str:
        return normalize_graph_relationship_type(relationship_type)

    def require_supported_relationship_type(self, relationship_type: str) -> str:
        return require_graph_relationship_type(
            relationship_type,
            error_type=UnsupportedGraphRelationshipType,
        )

    def require_supported_direction(self, direction: str) -> str:
        return require_graph_direction(direction, error_type=UnsupportedGraphDirection)

    def require_supported_result_side(self, result_side: str) -> str:
        return require_graph_result_side(
            result_side,
            error_type=UnsupportedGraphResultSide,
        )

    async def upsert_edge(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        payload: KnowledgeGraphEdgeCreate,
    ) -> KnowledgeGraphEdgeRecord:
        source_asset_type = self.fair_metadata_service.require_supported_asset_type(
            payload.source_asset_type
        )
        target_asset_type = self.fair_metadata_service.require_supported_asset_type(
            payload.target_asset_type
        )
        relationship_type = self.require_supported_relationship_type(payload.relationship_type)
        return await self._adapter(db).upsert_edge(
            KnowledgeGraphUpsertEdgeCommand(
                organization_id=organization_id,
                payload=payload.model_copy(
                    update={
                        "source_asset_type": source_asset_type,
                        "target_asset_type": target_asset_type,
                        "relationship_type": relationship_type,
                    }
                ),
            )
        )

    async def list_edges(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeGraphEdgeRecord]:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        return await self._adapter(db).list_edges(
            KnowledgeGraphEdgesListQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                limit=limit,
                offset=offset,
            )
        )

    async def get_facets(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
    ) -> KnowledgeGraphFacetResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )

        return await self._adapter(db).get_facets(
            KnowledgeGraphFacetsQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            )
        )

    async def get_neighborhood(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
        direction: str = "both",
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphNeighborhoodResponse:
        normalized_asset_type = self.fair_metadata_service.require_supported_asset_type(asset_type)
        normalized_direction = self.require_supported_direction(direction)
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        neighborhood = await self._adapter(db).get_neighborhood(
            KnowledgeGraphNeighborhoodQuery(
                organization_id=organization_id,
                asset_type=normalized_asset_type,
                asset_id=asset_id,
                direction=normalized_direction,
                relationship_type=normalized_relationship,
                limit=limit,
                offset=offset,
            )
        )
        return KnowledgeGraphNeighborhoodResponse(
            asset_type=neighborhood.asset_type,
            asset_id=neighborhood.asset_id,
            direction=neighborhood.direction,
            relationship_type=neighborhood.relationship_type,
            outgoing_edges=neighborhood.outgoing_edges,
            incoming_edges=neighborhood.incoming_edges,
            edge_count=neighborhood.edge_count,
        )

    async def build_evidence_pack(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
        direction: str = "both",
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphEvidencePackResponse:
        normalized_asset_type = self.fair_metadata_service.require_supported_asset_type(asset_type)
        normalized_direction = self.require_supported_direction(direction)
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        return await self._adapter(db).build_evidence_pack(
            KnowledgeGraphEvidencePackQuery(
                organization_id=organization_id,
                asset_type=normalized_asset_type,
                asset_id=asset_id,
                direction=normalized_direction,
                relationship_type=normalized_relationship,
                limit=limit,
                offset=offset,
            )
        )

    async def search_evidence(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphEvidenceSearchResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        return await self._adapter(db).search_evidence(
            KnowledgeGraphEvidenceSearchQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                limit=limit,
                offset=offset,
            )
        )

    async def build_retrieval_candidates(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        candidate_direction: str = "both",
        limit: int = 100,
        offset: int = 0,
        candidate_edge_limit: int = 100,
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        normalized_candidate_direction = self.require_supported_direction(candidate_direction)
        return await self._adapter(db).build_retrieval_candidates(
            KnowledgeGraphRetrievalCandidatesQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                candidate_direction=normalized_candidate_direction,
                limit=limit,
                offset=offset,
                candidate_edge_limit=candidate_edge_limit,
            )
        )

    async def build_retrieval_diagnostics(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        candidate_direction: str = "both",
        minimum_confidence: float = 0.5,
        limit: int = 100,
        offset: int = 0,
        candidate_edge_limit: int = 100,
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        normalized_candidate_direction = self.require_supported_direction(candidate_direction)
        return await self._adapter(db).build_retrieval_diagnostics(
            KnowledgeGraphRetrievalDiagnosticsQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                candidate_direction=normalized_candidate_direction,
                minimum_confidence=minimum_confidence,
                limit=limit,
                offset=offset,
                candidate_edge_limit=candidate_edge_limit,
            )
        )

    async def rank_retrieval_candidates(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        candidate_direction: str = "both",
        limit: int = 100,
        offset: int = 0,
        candidate_edge_limit: int = 100,
    ) -> KnowledgeGraphRankedCandidateResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        normalized_candidate_direction = self.require_supported_direction(candidate_direction)
        return await self._adapter(db).rank_retrieval_candidates(
            KnowledgeGraphRankedCandidatesQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                candidate_direction=normalized_candidate_direction,
                limit=limit,
                offset=offset,
                candidate_edge_limit=candidate_edge_limit,
            )
        )

    async def build_reevu_dry_run_preview(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        prompt: str | None = None,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        candidate_direction: str = "both",
        minimum_confidence: float = 0.5,
        limit: int = 100,
        offset: int = 0,
        candidate_edge_limit: int = 100,
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        normalized_candidate_direction = self.require_supported_direction(candidate_direction)
        return await self._adapter(db).build_reevu_dry_run_preview(
            KnowledgeGraphReevuDryRunPreviewQuery(
                organization_id=organization_id,
                prompt=prompt,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                candidate_direction=normalized_candidate_direction,
                minimum_confidence=minimum_confidence,
                limit=limit,
                offset=offset,
                candidate_edge_limit=candidate_edge_limit,
            )
        )

    async def build_explorer_snapshot(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        candidate_direction: str = "both",
        minimum_confidence: float = 0.5,
        limit: int = 100,
        offset: int = 0,
        candidate_edge_limit: int = 100,
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        normalized_source_type = (
            self.fair_metadata_service.require_supported_asset_type(source_asset_type)
            if source_asset_type
            else None
        )
        normalized_target_type = (
            self.fair_metadata_service.require_supported_asset_type(target_asset_type)
            if target_asset_type
            else None
        )
        normalized_relationship = (
            self.require_supported_relationship_type(relationship_type)
            if relationship_type
            else None
        )
        normalized_result_side = self.require_supported_result_side(result_side)
        normalized_candidate_direction = self.require_supported_direction(candidate_direction)
        return await self._adapter(db).build_explorer_snapshot(
            KnowledgeGraphExplorerSnapshotQuery(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
                result_side=normalized_result_side,
                candidate_direction=normalized_candidate_direction,
                minimum_confidence=minimum_confidence,
                limit=limit,
                offset=offset,
                candidate_edge_limit=candidate_edge_limit,
            )
        )
