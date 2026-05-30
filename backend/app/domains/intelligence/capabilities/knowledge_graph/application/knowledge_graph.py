"""Intelligence Knowledge Graph use cases."""

import json

from app.domains.intelligence.capabilities.knowledge_graph.ports.knowledge_graph import (
    KnowledgeGraphEdgesListReader,
    KnowledgeGraphEdgeWriter,
    KnowledgeGraphEvidencePackDataSource,
    KnowledgeGraphEvidencePackReader,
    KnowledgeGraphEvidenceSearchDataSource,
    KnowledgeGraphEvidenceSearchReader,
    KnowledgeGraphExplorerSnapshotReader,
    KnowledgeGraphFacetsReader,
    KnowledgeGraphNeighborhoodReader,
    KnowledgeGraphRankedCandidatesReader,
    KnowledgeGraphReevuDryRunPreviewReader,
    KnowledgeGraphRetrievalCandidateDataSource,
    KnowledgeGraphRetrievalCandidatesReader,
    KnowledgeGraphRetrievalDiagnosticsReader,
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
    KnowledgeGraphRankedCandidateResponse,
    KnowledgeGraphRankedCandidatesQuery,
    KnowledgeGraphReevuDryRunPreviewQuery,
    KnowledgeGraphReevuDryRunPreviewResponse,
    KnowledgeGraphRetrievalCandidate,
    KnowledgeGraphRetrievalCandidateResponse,
    KnowledgeGraphRetrievalCandidatesQuery,
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
                    matched_edge=edge,
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
        return await self._reader.list_edges(query)


class KnowledgeGraphUpsertEdgeUseCase:
    """Create or update a Knowledge Graph edge through an Intelligence-owned port."""

    def __init__(self, writer: KnowledgeGraphEdgeWriter) -> None:
        self._writer = writer

    async def execute(self, command: KnowledgeGraphUpsertEdgeCommand) -> KnowledgeGraphEdgeResponse:
        return await self._writer.upsert_edge(command)


class KnowledgeGraphNeighborhoodUseCase:
    """Build a Knowledge Graph neighborhood through an Intelligence-owned port."""

    def __init__(self, reader: KnowledgeGraphNeighborhoodReader) -> None:
        self._reader = reader

    async def execute(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodResponse:
        return await self._reader.get_neighborhood(query)


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
