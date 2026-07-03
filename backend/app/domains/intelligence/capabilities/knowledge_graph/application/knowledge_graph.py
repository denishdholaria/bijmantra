"""Intelligence Knowledge Graph use cases."""

import json

from app.domains.intelligence.capabilities.knowledge_graph.domain.knowledge_graph_retrieval import (
    candidate_diagnostic_warnings,
    candidate_retrieval_score,
    candidate_score_factors,
    retrieval_readiness,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.knowledge_graph import (
    KnowledgeGraphEdgesListReader,
    KnowledgeGraphEdgeWriter,
    KnowledgeGraphEvidencePackDataSource,
    KnowledgeGraphEvidencePackReader,
    KnowledgeGraphEvidenceSearchDataSource,
    KnowledgeGraphEvidenceSearchReader,
    KnowledgeGraphExplorerSnapshotDataSource,
    KnowledgeGraphExplorerSnapshotReader,
    KnowledgeGraphFacetsReader,
    KnowledgeGraphNeighborhoodReader,
    KnowledgeGraphRankedCandidatesReader,
    KnowledgeGraphReevuDryRunPreviewDataSource,
    KnowledgeGraphReevuDryRunPreviewReader,
    KnowledgeGraphRetrievalCandidateDataSource,
    KnowledgeGraphRetrievalCandidatesReader,
    KnowledgeGraphRetrievalDiagnosticsReader,
)
from app.domains.intelligence.capabilities.knowledge_graph.ports.records import (
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphNeighborhoodRecord,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphEvidenceSearchResult,
    KnowledgeGraphExplorerSnapshotQuery,
    KnowledgeGraphExplorerSnapshotResponse,
    KnowledgeGraphFacetResponse,
    KnowledgeGraphFacetsQuery,
    KnowledgeGraphNeighborhoodQuery,
    KnowledgeGraphNeighborhoodResponse,
    KnowledgeGraphRankedCandidate,
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidate,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
    KnowledgeGraphRetrievalDiagnosticCandidate,
    KnowledgeGraphRetrievalDiagnosticsQuery,
    KnowledgeGraphRetrievalDiagnosticsResponse,
    KnowledgeGraphUpsertEdgeCommand,
)


class KnowledgeGraphExplorerSnapshotUseCase:
    """Build a Knowledge Graph explorer snapshot through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphExplorerSnapshotReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        return await self._reader.build_explorer_snapshot(query)


class KnowledgeGraphRankedCandidatesUseCase:
    """Rank Knowledge Graph retrieval candidates through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphRankedCandidatesReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        return await self._reader.rank_retrieval_candidates(query)


class KnowledgeGraphRetrievalDiagnosticsUseCase:
    """Build Knowledge Graph retrieval diagnostics through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphRetrievalDiagnosticsReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        return await self._reader.build_retrieval_diagnostics(query)


class KnowledgeGraphRetrievalCandidatesUseCase:
    """Build Knowledge Graph retrieval candidates through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphRetrievalCandidatesReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        return await self._reader.build_retrieval_candidates(query)


class KnowledgeGraphEvidenceSearchUseCase:
    """Search Knowledge Graph evidence through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphEvidenceSearchReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        return await self._reader.search_evidence(query)


class KnowledgeGraphEvidenceSearchBuilder:
    """Build evidence-search responses from normalized graph edge ports."""

    def __init__(self, data_source: KnowledgeGraphEvidenceSearchDataSource) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        result_side = self._data_source.normalize_result_side(query.result_side)
        source_asset_type = (
            self._data_source.normalize_asset_type(query.source_asset_type)
            if query.source_asset_type
            else None
        )
        target_asset_type = (
            self._data_source.normalize_asset_type(query.target_asset_type)
            if query.target_asset_type
            else None
        )
        relationship_type = (
            self._data_source.normalize_relationship_type(query.relationship_type)
            if query.relationship_type
            else None
        )
        edges = await self._data_source.list_edges(
            KnowledgeGraphEdgesListQuery(
                organization_id=query.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=relationship_type,
                limit=query.limit,
                offset=query.offset,
            )
        )

        results: list[KnowledgeGraphEvidenceSearchResult] = []
        for edge in edges:
            if result_side == "source":
                result_asset_type = edge.source_asset_type
                result_asset_id = edge.source_asset_id
            else:
                result_asset_type = edge.target_asset_type
                result_asset_id = edge.target_asset_id
            metadata = await self._data_source.require_fair_asset(
                organization_id=query.organization_id,
                asset_type=result_asset_type,
                asset_id=result_asset_id,
            )
            results.append(
                KnowledgeGraphEvidenceSearchResult(
                    asset_type=result_asset_type,
                    asset_id=result_asset_id,
                    asset_title=metadata.asset_title,
                    persistent_identifier=metadata.persistent_identifier,
                    relationship_type=edge.relationship_type,
                    matched_edge=_edge_response_from_record(edge),
                    evidence_refs=list(edge.evidence_refs or []),
                    provenance=dict(edge.provenance or {}),
                    confidence=edge.confidence,
                    derivation_method=edge.derivation_method,
                )
            )

        return KnowledgeGraphEvidenceSearchResponse(
            source_asset_type=source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=relationship_type,
            result_side=result_side,
            results=results,
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
            result_count=len(results),
        )


class KnowledgeGraphEvidencePackUseCase:
    """Build a Knowledge Graph evidence pack through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphEvidencePackReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        return await self._reader.build_evidence_pack(query)


class KnowledgeGraphEvidencePackBuilder:
    """Build evidence packs from neighborhood and FAIR asset ports."""

    def __init__(self, data_source: KnowledgeGraphEvidencePackDataSource) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        asset_type = self._data_source.normalize_asset_type(query.asset_type)
        asset_metadata = await self._data_source.require_fair_asset(
            organization_id=query.organization_id,
            asset_type=asset_type,
            asset_id=query.asset_id,
        )
        neighborhood = await self._data_source.get_neighborhood(
            KnowledgeGraphNeighborhoodQuery(
                organization_id=query.organization_id,
                asset_type=asset_type,
                asset_id=query.asset_id,
                direction=query.direction,
                relationship_type=query.relationship_type,
                limit=query.limit,
                offset=query.offset,
            )
        )
        neighborhood = _neighborhood_response_from_record(neighborhood)
        edges = [*neighborhood.outgoing_edges, *neighborhood.incoming_edges]
        evidence_refs = _deduplicate_evidence_refs(edges)
        relationship_types = sorted({edge.relationship_type for edge in edges})

        return KnowledgeGraphEvidencePackResponse(
            asset_type=asset_type,
            asset_id=query.asset_id,
            asset_title=asset_metadata.asset_title,
            persistent_identifier=asset_metadata.persistent_identifier,
            direction=neighborhood.direction,
            relationship_type=neighborhood.relationship_type,
            neighborhood=neighborhood,
            relationship_types=relationship_types,
            evidence_refs=evidence_refs,
            retrieval_policy={
                "graphDepth": 1,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
            edge_count=neighborhood.edge_count,
        )


class KnowledgeGraphFacetsUseCase:
    """Build Knowledge Graph facets through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphFacetsReader) -> None:
        self._reader = reader

    async def execute(self, query: KnowledgeGraphFacetsQuery) -> KnowledgeGraphFacetResponse:
        return await self._reader.get_facets(query)


class KnowledgeGraphEdgesListUseCase:
    """List Knowledge Graph edges through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphEdgesListReader) -> None:
        self._reader = reader

    async def execute(self, query: KnowledgeGraphEdgesListQuery) -> list[KnowledgeGraphEdgeResponse]:
        return [
            _edge_response_from_record(edge)
            for edge in await self._reader.list_edges(query)
        ]


class KnowledgeGraphUpsertEdgeUseCase:
    """Create or update a Knowledge Graph edge through an Intelligence-owned port."""

    def __init__(self, writer: KnowledgeGraphEdgeWriter) -> None:
        self._writer = writer

    async def execute(self, command: KnowledgeGraphUpsertEdgeCommand) -> KnowledgeGraphEdgeResponse:
        return _edge_response_from_record(await self._writer.upsert_edge(command))


class KnowledgeGraphNeighborhoodUseCase:
    """Build a Knowledge Graph neighborhood through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphNeighborhoodReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodResponse:
        return _neighborhood_response_from_record(await self._reader.get_neighborhood(query))


class KnowledgeGraphRetrievalCandidatesBuilder:
    """Build retrieval candidates from evidence search and evidence-pack ports."""

    def __init__(self, data_source: KnowledgeGraphRetrievalCandidateDataSource) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphRetrievalCandidatesQuery
    ) -> KnowledgeGraphRetrievalCandidateResponse:
        search_results = await self._data_source.search_evidence(
            KnowledgeGraphEvidenceSearchQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                limit=query.limit,
                offset=query.offset,
            )
        )
        candidate_direction = self._data_source.normalize_direction(
            query.candidate_direction
        )

        grouped_results = {}
        for result in search_results.results:
            grouped_results.setdefault((result.asset_type, result.asset_id), []).append(
                result
            )

        candidates: list[KnowledgeGraphRetrievalCandidate] = []
        for (asset_type, asset_id), results in grouped_results.items():
            first_result = results[0]
            matched_edges = [result.matched_edge for result in results]
            evidence_pack = await self._data_source.build_evidence_pack(
                KnowledgeGraphEvidencePackQuery(
                    organization_id=query.organization_id,
                    asset_type=asset_type,
                    asset_id=asset_id,
                    direction=candidate_direction,
                    relationship_type=None,
                    limit=query.candidate_edge_limit,
                    offset=0,
                )
            )
            candidates.append(
                KnowledgeGraphRetrievalCandidate(
                    asset_type=asset_type,
                    asset_id=asset_id,
                    asset_title=first_result.asset_title,
                    persistent_identifier=first_result.persistent_identifier,
                    matched_edges=matched_edges,
                    matched_evidence_refs=_deduplicate_evidence_refs(matched_edges),
                    evidence_pack=evidence_pack,
                    match_count=len(results),
                )
            )

        return KnowledgeGraphRetrievalCandidateResponse(
            source_asset_type=search_results.source_asset_type,
            source_asset_id=search_results.source_asset_id,
            target_asset_type=search_results.target_asset_type,
            target_asset_id=search_results.target_asset_id,
            relationship_type=search_results.relationship_type,
            result_side=search_results.result_side,
            candidate_direction=candidate_direction,
            candidates=candidates,
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "candidateUseOnly": True,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
            search_result_count=search_results.result_count,
            candidate_count=len(candidates),
        )


class KnowledgeGraphRankedCandidatesBuilder:
    """Rank retrieval candidates using deterministic Knowledge Graph policy."""

    def __init__(self, data_source: KnowledgeGraphRetrievalCandidatesReader) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphRankedCandidatesQuery
    ) -> KnowledgeGraphRankedCandidateResponse:
        candidates = await self._data_source.build_retrieval_candidates(
            KnowledgeGraphRetrievalCandidatesQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
        )
        scored_candidates: list[
            tuple[float, dict[str, float], KnowledgeGraphRetrievalCandidate]
        ] = []
        for candidate in candidates.candidates:
            factors = candidate_score_factors(
                match_count=candidate.match_count,
                confidence_values=[
                    edge.confidence
                    for edge in candidate.matched_edges
                    if edge.confidence is not None
                ],
                matched_evidence_ref_count=len(candidate.matched_evidence_refs),
                evidence_pack_edge_count=candidate.evidence_pack.edge_count,
            )
            scored_candidates.append((candidate_retrieval_score(factors), factors, candidate))

        scored_candidates.sort(
            key=lambda item: (-item[0], item[2].asset_type, item[2].asset_id)
        )
        return KnowledgeGraphRankedCandidateResponse(
            candidates=candidates,
            ranked_candidates=[
                KnowledgeGraphRankedCandidate(
                    rank=index,
                    candidate=candidate,
                    retrieval_score=score,
                    score_factors=factors,
                )
                for index, (score, factors, candidate) in enumerate(
                    scored_candidates,
                    start=1,
                )
            ],
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


class KnowledgeGraphRetrievalDiagnosticsBuilder:
    """Summarize retrieval quality using deterministic Knowledge Graph policy."""

    def __init__(self, data_source: KnowledgeGraphRetrievalCandidatesReader) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphRetrievalDiagnosticsQuery
    ) -> KnowledgeGraphRetrievalDiagnosticsResponse:
        candidates = await self._data_source.build_retrieval_candidates(
            KnowledgeGraphRetrievalCandidatesQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
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
                elif edge.confidence < query.minimum_confidence:
                    low_confidence_edge_count += 1
                    candidate_low_confidence_edge_count += 1

            total_matched_evidence_refs += len(candidate.matched_evidence_refs)
            candidate_diagnostics.append(
                KnowledgeGraphRetrievalDiagnosticCandidate(
                    asset_type=candidate.asset_type,
                    asset_id=candidate.asset_id,
                    asset_title=candidate.asset_title,
                    persistent_identifier=candidate.persistent_identifier,
                    matched_edge_count=len(candidate.matched_edges),
                    matched_evidence_ref_count=len(candidate.matched_evidence_refs),
                    matched_edges_without_evidence_count=(
                        candidate_edges_without_evidence_count
                    ),
                    low_confidence_edge_count=candidate_low_confidence_edge_count,
                    missing_confidence_edge_count=candidate_missing_confidence_edge_count,
                    evidence_pack_edge_count=candidate.evidence_pack.edge_count,
                    warnings=candidate_diagnostic_warnings(
                        matched_edges_without_evidence_count=(
                            candidate_edges_without_evidence_count
                        ),
                        low_confidence_edge_count=candidate_low_confidence_edge_count,
                        missing_confidence_edge_count=(
                            candidate_missing_confidence_edge_count
                        ),
                    ),
                )
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
            readiness=retrieval_readiness(
                candidate_count=candidates.candidate_count,
                matched_edges_without_evidence_count=matched_edges_without_evidence_count,
                low_confidence_edge_count=low_confidence_edge_count,
                missing_confidence_edge_count=missing_confidence_edge_count,
            ),
            retrieval_policy={
                "graphDepth": 1,
                "searchMode": "edge_filter",
                "candidateUseOnly": True,
                "diagnosticOnly": True,
                "rawDataImported": False,
                "trustedReevuSurfaceExpanded": False,
            },
        )


class KnowledgeGraphReevuDryRunPreviewBuilder:
    """Build a REEVU dry-run preview without invoking the REEVU runtime."""

    def __init__(self, data_source: KnowledgeGraphReevuDryRunPreviewDataSource) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        ranked_candidates = await self._data_source.rank_retrieval_candidates(
            KnowledgeGraphRankedCandidatesQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
        )
        diagnostics = await self._data_source.build_retrieval_diagnostics(
            KnowledgeGraphRetrievalDiagnosticsQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                minimum_confidence=query.minimum_confidence,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
        )
        return KnowledgeGraphReevuDryRunPreviewResponse(
            prompt=query.prompt,
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


class KnowledgeGraphExplorerSnapshotBuilder:
    """Build a UI-ready Knowledge Graph explorer snapshot."""

    def __init__(self, data_source: KnowledgeGraphExplorerSnapshotDataSource) -> None:
        self._data_source = data_source

    async def execute(
        self, query: KnowledgeGraphExplorerSnapshotQuery
    ) -> KnowledgeGraphExplorerSnapshotResponse:
        facets = await self._data_source.get_facets(
            KnowledgeGraphFacetsQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
            )
        )
        ranked_candidates = await self._data_source.rank_retrieval_candidates(
            KnowledgeGraphRankedCandidatesQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
        )
        diagnostics = await self._data_source.build_retrieval_diagnostics(
            KnowledgeGraphRetrievalDiagnosticsQuery(
                organization_id=query.organization_id,
                source_asset_type=query.source_asset_type,
                source_asset_id=query.source_asset_id,
                target_asset_type=query.target_asset_type,
                target_asset_id=query.target_asset_id,
                relationship_type=query.relationship_type,
                result_side=query.result_side,
                candidate_direction=query.candidate_direction,
                minimum_confidence=query.minimum_confidence,
                limit=query.limit,
                offset=query.offset,
                candidate_edge_limit=query.candidate_edge_limit,
            )
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


class KnowledgeGraphReevuDryRunPreviewUseCase:
    """Build a REEVU dry-run preview through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphReevuDryRunPreviewReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphReevuDryRunPreviewQuery
    ) -> KnowledgeGraphReevuDryRunPreviewResponse:
        return await self._reader.build_reevu_dry_run_preview(query)


def _deduplicate_evidence_refs(edges: list[object]) -> list[dict[str, object]]:
    seen: set[str] = set()
    evidence_refs: list[dict[str, object]] = []
    for edge in edges:
        for evidence_ref in getattr(edge, "evidence_refs", None) or []:
            key = json.dumps(evidence_ref, sort_keys=True, separators=(",", ":"), default=str)
            if key in seen:
                continue
            seen.add(key)
            evidence_refs.append(dict(evidence_ref))
    return evidence_refs


def _edge_response_from_record(record: KnowledgeGraphEdgeRecord) -> KnowledgeGraphEdgeResponse:
    return KnowledgeGraphEdgeResponse(
        id=record.id,
        organization_id=record.organization_id,
        edge_id=record.edge_id,
        source_asset_type=record.source_asset_type,
        source_asset_id=record.source_asset_id,
        relationship_type=record.relationship_type,
        target_asset_type=record.target_asset_type,
        target_asset_id=record.target_asset_id,
        evidence_refs=list(record.evidence_refs or []),
        provenance=dict(record.provenance or {}),
        confidence=record.confidence,
        derivation_method=record.derivation_method,
        status=record.status,
        schema_version=record.schema_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _neighborhood_response_from_record(
    record: KnowledgeGraphNeighborhoodRecord,
) -> KnowledgeGraphNeighborhoodResponse:
    return KnowledgeGraphNeighborhoodResponse(
        asset_type=record.asset_type,
        asset_id=record.asset_id,
        direction=record.direction,
        relationship_type=record.relationship_type,
        outgoing_edges=[
            _edge_response_from_record(edge) for edge in record.outgoing_edges
        ],
        incoming_edges=[
            _edge_response_from_record(edge) for edge in record.incoming_edges
        ],
        edge_count=record.edge_count,
    )
