"""Tenant-scoped agricultural knowledge graph edge service."""

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph_legacy import (
    LegacyKnowledgeGraphEvidencePackDataSource,
    LegacyKnowledgeGraphEvidenceSearchDataSource,
    LegacyKnowledgeGraphRetrievalDataSource,
)
from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph_persistence import (
    SqlAlchemyKnowledgeGraphPersistence,
)
from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphEvidencePackBuilder,
    KnowledgeGraphEvidenceSearchBuilder,
    KnowledgeGraphRetrievalCandidatesBuilder,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    candidate_diagnostic_warnings as intelligence_candidate_diagnostic_warnings,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    candidate_retrieval_score as intelligence_candidate_retrieval_score,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    candidate_score_factors as intelligence_candidate_score_factors,
)
from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    retrieval_readiness as intelligence_retrieval_readiness,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    GraphAssetNotFound as GraphAssetNotFound,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphRetrievalCandidatesQuery,
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
from app.models.knowledge_graph import AgriculturalKnowledgeGraphEdge
from app.schemas.knowledge_graph import (
    SUPPORTED_GRAPH_DIRECTIONS,
    SUPPORTED_GRAPH_RELATIONSHIP_TYPES,
    SUPPORTED_GRAPH_RESULT_SIDES,
    KnowledgeGraphEdgeCreate,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphExplorerSnapshotResponse,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphNeighborhoodResponse,
    KnowledgeGraphRankedCandidate,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidate,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalDiagnosticCandidate,
    KnowledgeGraphRetrievalDiagnosticsResponse,
)


class UnsupportedGraphRelationshipType(ValueError):
    """Raised when a graph relationship is outside the first supported vocabulary."""


class UnsupportedGraphDirection(ValueError):
    """Raised when a neighborhood direction is outside the supported one-hop modes."""


class UnsupportedGraphResultSide(ValueError):
    """Raised when evidence search asks for an unsupported result projection side."""


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_digest(data: Any) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


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

    def _persistence(self, db: AsyncSession) -> SqlAlchemyKnowledgeGraphPersistence:
        return SqlAlchemyKnowledgeGraphPersistence(
            db,
            fair_metadata_repository=self._fair_metadata_repository(db),
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
        return await self._persistence(db).require_fair_asset(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )

    def normalize_relationship_type(self, relationship_type: str) -> str:
        return relationship_type.strip().lower().replace("-", "_").replace(" ", "_")

    def require_supported_relationship_type(self, relationship_type: str) -> str:
        normalized = self.normalize_relationship_type(relationship_type)
        if normalized not in SUPPORTED_GRAPH_RELATIONSHIP_TYPES:
            supported = ", ".join(SUPPORTED_GRAPH_RELATIONSHIP_TYPES)
            raise UnsupportedGraphRelationshipType(
                f"Unsupported graph relationship type '{relationship_type}'. Use: {supported}"
            )
        return normalized

    def require_supported_direction(self, direction: str) -> str:
        normalized = direction.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized not in SUPPORTED_GRAPH_DIRECTIONS:
            supported = ", ".join(SUPPORTED_GRAPH_DIRECTIONS)
            raise UnsupportedGraphDirection(
                f"Unsupported graph neighborhood direction '{direction}'. Use: {supported}"
            )
        return normalized

    def require_supported_result_side(self, result_side: str) -> str:
        normalized = result_side.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized not in SUPPORTED_GRAPH_RESULT_SIDES:
            supported = ", ".join(SUPPORTED_GRAPH_RESULT_SIDES)
            raise UnsupportedGraphResultSide(
                f"Unsupported graph evidence-search result side '{result_side}'. Use: {supported}"
            )
        return normalized

    async def upsert_edge(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        payload: KnowledgeGraphEdgeCreate,
    ) -> AgriculturalKnowledgeGraphEdge:
        source_asset_type = self.fair_metadata_service.require_supported_asset_type(
            payload.source_asset_type
        )
        target_asset_type = self.fair_metadata_service.require_supported_asset_type(
            payload.target_asset_type
        )
        relationship_type = self.require_supported_relationship_type(payload.relationship_type)

        persistence = self._persistence(db)
        await persistence.require_fair_asset(
            organization_id=organization_id,
            asset_type=source_asset_type,
            asset_db_id=payload.source_asset_id,
        )
        await persistence.require_fair_asset(
            organization_id=organization_id,
            asset_type=target_asset_type,
            asset_db_id=payload.target_asset_id,
        )

        edge_id = self._edge_id(
            source_asset_type=source_asset_type,
            source_asset_id=payload.source_asset_id,
            relationship_type=relationship_type,
            target_asset_type=target_asset_type,
            target_asset_id=payload.target_asset_id,
        )
        return await persistence.upsert_edge(
            organization_id=organization_id,
            payload=payload,
            source_asset_type=source_asset_type,
            target_asset_type=target_asset_type,
            relationship_type=relationship_type,
            edge_id=edge_id,
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
    ) -> list[AgriculturalKnowledgeGraphEdge]:
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
        return await self._persistence(db).list_edges(
            organization_id=organization_id,
            source_asset_type=normalized_source_type,
            source_asset_id=source_asset_id,
            target_asset_type=normalized_target_type,
            target_asset_id=target_asset_id,
            relationship_type=normalized_relationship,
            limit=limit,
            offset=offset,
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

        persistence = self._persistence(db)
        total_edge_count = await persistence.count_edges(
            organization_id=organization_id,
            source_asset_type=normalized_source_type,
            source_asset_id=source_asset_id,
            target_asset_type=normalized_target_type,
            target_asset_id=target_asset_id,
            relationship_type=normalized_relationship,
        )
        return KnowledgeGraphFacetResponse(
            source_asset_type=normalized_source_type,
            source_asset_id=source_asset_id,
            target_asset_type=normalized_target_type,
            target_asset_id=target_asset_id,
            relationship_type=normalized_relationship,
            total_edge_count=total_edge_count,
            relationship_type_counts=await persistence.count_by_edge_column(
                column_name="relationship_type",
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            source_asset_type_counts=await persistence.count_by_edge_column(
                column_name="source_asset_type",
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            target_asset_type_counts=await persistence.count_by_edge_column(
                column_name="target_asset_type",
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            status_counts=await persistence.count_by_edge_column(
                column_name="status",
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            derivation_method_counts=await persistence.count_by_edge_column(
                column_name="derivation_method",
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            asset_type_pair_counts=await persistence.count_asset_type_pairs(
                organization_id=organization_id,
                source_asset_type=normalized_source_type,
                source_asset_id=source_asset_id,
                target_asset_type=normalized_target_type,
                target_asset_id=target_asset_id,
                relationship_type=normalized_relationship,
            ),
            retrieval_policy={
                "graphDepth": 1,
                "facetOnly": True,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
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
        persistence = self._persistence(db)
        await persistence.require_fair_asset(
            organization_id=organization_id,
            asset_type=normalized_asset_type,
            asset_db_id=asset_id,
        )

        outgoing_edges: list[AgriculturalKnowledgeGraphEdge] = []
        incoming_edges: list[AgriculturalKnowledgeGraphEdge] = []
        if normalized_direction in {"outgoing", "both"}:
            outgoing_edges = await persistence.list_neighborhood_edges(
                organization_id=organization_id,
                asset_type=normalized_asset_type,
                asset_id=asset_id,
                relationship_type=normalized_relationship,
                incoming=False,
                limit=limit,
                offset=offset,
            )
        if normalized_direction in {"incoming", "both"}:
            incoming_edges = await persistence.list_neighborhood_edges(
                organization_id=organization_id,
                asset_type=normalized_asset_type,
                asset_id=asset_id,
                relationship_type=normalized_relationship,
                incoming=True,
                limit=limit,
                offset=offset,
            )

        return KnowledgeGraphNeighborhoodResponse(
            asset_type=normalized_asset_type,
            asset_id=asset_id,
            direction=normalized_direction,
            relationship_type=normalized_relationship,
            outgoing_edges=outgoing_edges,
            incoming_edges=incoming_edges,
            edge_count=len(outgoing_edges) + len(incoming_edges),
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
        builder = KnowledgeGraphEvidencePackBuilder(
            LegacyKnowledgeGraphEvidencePackDataSource(db=db, service=self)
        )
        return await builder.execute(
            KnowledgeGraphEvidencePackQuery(
                organization_id=organization_id,
                asset_type=asset_type,
                asset_id=asset_id,
                direction=direction,
                relationship_type=relationship_type,
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
        builder = KnowledgeGraphEvidenceSearchBuilder(
            LegacyKnowledgeGraphEvidenceSearchDataSource(db=db, service=self)
        )
        return await builder.execute(
            KnowledgeGraphEvidenceSearchQuery(
                organization_id=organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=target_asset_id,
                relationship_type=relationship_type,
                result_side=result_side,
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
        builder = KnowledgeGraphRetrievalCandidatesBuilder(
            LegacyKnowledgeGraphRetrievalDataSource(db=db, service=self)
        )
        return await builder.execute(
            KnowledgeGraphRetrievalCandidatesQuery(
                organization_id=organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=target_asset_id,
                relationship_type=relationship_type,
                result_side=result_side,
                candidate_direction=candidate_direction,
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
        candidates = await self.build_retrieval_candidates(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        relationship_type_counts: dict[str, int] = {}
        total_matched_edges = 0
        total_matched_evidence_refs = 0
        matched_edges_without_evidence_count = 0
        low_confidence_edge_count = 0
        missing_confidence_edge_count = 0
        candidate_diagnostics: list[KnowledgeGraphRetrievalDiagnosticCandidate] = []

        for candidate in candidates.candidates:
            candidate_edges_without_evidence_count = 0
            candidate_low_confidence_edge_count = 0
            candidate_missing_confidence_edge_count = 0
            for edge in candidate.matched_edges:
                total_matched_edges += 1
                relationship_type_counts[edge.relationship_type] = (
                    relationship_type_counts.get(edge.relationship_type, 0) + 1
                )
                if not edge.evidence_refs:
                    matched_edges_without_evidence_count += 1
                    candidate_edges_without_evidence_count += 1
                if edge.confidence is None:
                    missing_confidence_edge_count += 1
                    candidate_missing_confidence_edge_count += 1
                elif edge.confidence < minimum_confidence:
                    low_confidence_edge_count += 1
                    candidate_low_confidence_edge_count += 1

            total_matched_evidence_refs += len(candidate.matched_evidence_refs)
            warnings = self._candidate_diagnostic_warnings(
                matched_edges_without_evidence_count=candidate_edges_without_evidence_count,
                low_confidence_edge_count=candidate_low_confidence_edge_count,
                missing_confidence_edge_count=candidate_missing_confidence_edge_count,
            )
            candidate_diagnostics.append(
                KnowledgeGraphRetrievalDiagnosticCandidate(
                    asset_type=candidate.asset_type,
                    asset_id=candidate.asset_id,
                    asset_title=candidate.asset_title,
                    persistent_identifier=candidate.persistent_identifier,
                    matched_edge_count=len(candidate.matched_edges),
                    matched_evidence_ref_count=len(candidate.matched_evidence_refs),
                    matched_edges_without_evidence_count=candidate_edges_without_evidence_count,
                    low_confidence_edge_count=candidate_low_confidence_edge_count,
                    missing_confidence_edge_count=candidate_missing_confidence_edge_count,
                    evidence_pack_edge_count=candidate.evidence_pack.edge_count,
                    warnings=warnings,
                )
            )

        readiness = self._retrieval_readiness(
            candidate_count=candidates.candidate_count,
            matched_edges_without_evidence_count=matched_edges_without_evidence_count,
            low_confidence_edge_count=low_confidence_edge_count,
            missing_confidence_edge_count=missing_confidence_edge_count,
        )
        return KnowledgeGraphRetrievalDiagnosticsResponse(
            candidates=candidates,
            relationship_type_counts=dict(sorted(relationship_type_counts.items())),
            total_matched_edges=total_matched_edges,
            total_matched_evidence_refs=total_matched_evidence_refs,
            matched_edges_without_evidence_count=matched_edges_without_evidence_count,
            low_confidence_edge_count=low_confidence_edge_count,
            missing_confidence_edge_count=missing_confidence_edge_count,
            candidate_diagnostics=candidate_diagnostics,
            readiness=readiness,
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "candidateUseOnly": True,
                "diagnosticOnly": True,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
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
        candidates = await self.build_retrieval_candidates(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        scored_candidates: list[tuple[float, dict[str, float], KnowledgeGraphRetrievalCandidate]] = []
        for candidate in candidates.candidates:
            factors = self._candidate_score_factors(candidate)
            score = self._candidate_retrieval_score(factors)
            scored_candidates.append((score, factors, candidate))

        scored_candidates.sort(
            key=lambda item: (-item[0], item[2].asset_type, item[2].asset_id)
        )
        ranked_candidates = [
            KnowledgeGraphRankedCandidate(
                rank=index,
                candidate=candidate,
                retrieval_score=score,
                score_factors=factors,
            )
            for index, (score, factors, candidate) in enumerate(scored_candidates, start=1)
        ]
        return KnowledgeGraphRankedCandidateResponse(
            candidates=candidates,
            ranked_candidates=ranked_candidates,
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "candidateUseOnly": True,
                "deterministicScoring": True,
                "truthScore": False,
                "modelGenerated": False,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
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
        ranked_candidates = await self.rank_retrieval_candidates(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        diagnostics = await self.build_retrieval_diagnostics(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            minimum_confidence=minimum_confidence,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        return KnowledgeGraphReevuDryRunPreviewResponse(
            prompt=prompt,
            ranked_candidates=ranked_candidates,
            diagnostics=diagnostics,
            preview_summary={
                "candidateCount": ranked_candidates.candidates.candidate_count,
                "rankedCandidateCount": len(ranked_candidates.ranked_candidates),
                "matchedEdgeCount": diagnostics.total_matched_edges,
                "matchedEvidenceRefCount": diagnostics.total_matched_evidence_refs,
                "readinessStatus": diagnostics.readiness.get("status"),
            },
            authority_boundary={
                "dryRunOnly": True,
                "answerGenerated": False,
                "reevuRuntimeInvoked": False,
                "trustedSurfaceExpanded": False,
                "benchmarkAuthorityChanged": False,
            },
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "candidateUseOnly": True,
                "dryRunOnly": True,
                "answerGenerated": False,
                "trustedReevuSurfaceExpanded": False,
            },
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
        facets = await self.get_facets(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
        )
        ranked_candidates = await self.rank_retrieval_candidates(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        diagnostics = await self.build_retrieval_diagnostics(
            db,
            organization_id=organization_id,
            source_asset_type=source_asset_type,
            source_asset_id=source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            candidate_direction=candidate_direction,
            minimum_confidence=minimum_confidence,
            limit=limit,
            offset=offset,
            candidate_edge_limit=candidate_edge_limit,
        )
        return KnowledgeGraphExplorerSnapshotResponse(
            facets=facets,
            ranked_candidates=ranked_candidates,
            diagnostics=diagnostics,
            snapshot_summary={
                "totalEdgeCount": facets.total_edge_count,
                "candidateCount": ranked_candidates.candidates.candidate_count,
                "rankedCandidateCount": len(ranked_candidates.ranked_candidates),
                "matchedEdgeCount": diagnostics.total_matched_edges,
                "matchedEvidenceRefCount": diagnostics.total_matched_evidence_refs,
                "readinessStatus": diagnostics.readiness.get("status"),
                "relationshipTypeCount": len(facets.relationship_type_counts),
                "sourceAssetTypeCount": len(facets.source_asset_type_counts),
                "targetAssetTypeCount": len(facets.target_asset_type_counts),
                "assetTypePairCount": len(facets.asset_type_pair_counts),
            },
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "explorerOnly": True,
                "answerGenerated": False,
                "reevuRuntimeInvoked": False,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
        )

    def _candidate_diagnostic_warnings(
        self,
        *,
        matched_edges_without_evidence_count: int,
        low_confidence_edge_count: int,
        missing_confidence_edge_count: int,
    ) -> list[str]:
        return intelligence_candidate_diagnostic_warnings(
            matched_edges_without_evidence_count=matched_edges_without_evidence_count,
            low_confidence_edge_count=low_confidence_edge_count,
            missing_confidence_edge_count=missing_confidence_edge_count,
        )

    def _retrieval_readiness(
        self,
        *,
        candidate_count: int,
        matched_edges_without_evidence_count: int,
        low_confidence_edge_count: int,
        missing_confidence_edge_count: int,
    ) -> dict[str, Any]:
        return intelligence_retrieval_readiness(
            candidate_count=candidate_count,
            matched_edges_without_evidence_count=matched_edges_without_evidence_count,
            low_confidence_edge_count=low_confidence_edge_count,
            missing_confidence_edge_count=missing_confidence_edge_count,
        )

    def _candidate_score_factors(
        self,
        candidate: KnowledgeGraphRetrievalCandidate,
    ) -> dict[str, float]:
        confidence_values = [
            edge.confidence for edge in candidate.matched_edges if edge.confidence is not None
        ]
        return intelligence_candidate_score_factors(
            match_count=candidate.match_count,
            confidence_values=confidence_values,
            matched_evidence_ref_count=len(candidate.matched_evidence_refs),
            evidence_pack_edge_count=candidate.evidence_pack.edge_count,
        )

    def _candidate_retrieval_score(self, factors: dict[str, float]) -> float:
        return intelligence_candidate_retrieval_score(factors)

    def _edge_id(
        self,
        *,
        source_asset_type: str,
        source_asset_id: str,
        relationship_type: str,
        target_asset_type: str,
        target_asset_id: str,
    ) -> str:
        digest = _sha256_digest(
            {
                "sourceAssetType": source_asset_type,
                "sourceAssetId": source_asset_id,
                "relationshipType": relationship_type,
                "targetAssetType": target_asset_type,
                "targetAssetId": target_asset_id,
            }
        )
        return f"kg-edge-{digest[:16]}"
