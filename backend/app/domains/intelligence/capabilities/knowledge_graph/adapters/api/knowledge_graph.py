"""Agricultural knowledge graph product API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.intelligence.capabilities.knowledge_graph.adapters.api.access import (
    require_knowledge_graph_api_access,
)
from app.domains.intelligence.capabilities.knowledge_graph.adapters.knowledge_graph import (
    SqlAlchemyKnowledgeGraphAdapter,
)
from app.domains.intelligence.capabilities.knowledge_graph.application.knowledge_graph import (
    KnowledgeGraphEdgesListUseCase,
    KnowledgeGraphEvidencePackUseCase,
    KnowledgeGraphEvidenceSearchUseCase,
    KnowledgeGraphExplorerSnapshotUseCase,
    KnowledgeGraphFacetsUseCase,
    KnowledgeGraphNeighborhoodUseCase,
    KnowledgeGraphRankedCandidatesUseCase,
    KnowledgeGraphReevuDryRunPreviewUseCase,
    KnowledgeGraphRetrievalCandidatesUseCase,
    KnowledgeGraphRetrievalDiagnosticsUseCase,
    KnowledgeGraphUpsertEdgeUseCase,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    GraphAssetNotFound,
    KnowledgeGraphEdgeCreate,
    KnowledgeGraphEdgeResponse,
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
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User


router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


def _raise_http_error(error: ValueError) -> None:
    if isinstance(error, GraphAssetNotFound):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/edges", response_model=KnowledgeGraphEdgeResponse)
async def create_knowledge_graph_edge(
    payload: KnowledgeGraphEdgeCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphEdgeResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.write",
        required_data_scopes=("organization", "asset", "evidence", "provenance"),
    )
    try:
        use_case = KnowledgeGraphUpsertEdgeUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphUpsertEdgeCommand(
                organization_id=current_user.organization_id,
                payload=payload,
            )
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/evidence-pack", response_model=KnowledgeGraphEvidencePackResponse)
async def get_knowledge_graph_evidence_pack(
    asset_type: str = Query(...),
    asset_id: str = Query(...),
    direction: str = Query("both"),
    relationship_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphEvidencePackResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphEvidencePackUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphEvidencePackQuery(
                organization_id=current_user.organization_id,
                asset_type=asset_type,
                asset_id=asset_id,
                direction=direction,
                relationship_type=relationship_type,
                limit=limit,
                offset=offset,
            )
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/facets", response_model=KnowledgeGraphFacetResponse)
async def get_knowledge_graph_facets(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphFacetResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset"),
    )
    try:
        use_case = KnowledgeGraphFacetsUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphFacetsQuery(
                organization_id=current_user.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=target_asset_id,
                relationship_type=relationship_type,
            )
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/explorer-snapshot", response_model=KnowledgeGraphExplorerSnapshotResponse)
async def get_knowledge_graph_explorer_snapshot(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    candidate_direction: str = Query("both"),
    minimum_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    candidate_edge_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphExplorerSnapshotResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphExplorerSnapshotUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphExplorerSnapshotQuery(
                organization_id=current_user.organization_id,
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
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/reevu-dry-run-preview", response_model=KnowledgeGraphReevuDryRunPreviewResponse)
async def get_knowledge_graph_reevu_dry_run_preview(
    prompt: str | None = Query(None),
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    candidate_direction: str = Query("both"),
    minimum_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    candidate_edge_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphReevuDryRunPreviewResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphReevuDryRunPreviewUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphReevuDryRunPreviewQuery(
                organization_id=current_user.organization_id,
                prompt=prompt,
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
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/ranked-candidates", response_model=KnowledgeGraphRankedCandidateResponse)
async def get_knowledge_graph_ranked_candidates(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    candidate_direction: str = Query("both"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    candidate_edge_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphRankedCandidateResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphRankedCandidatesUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphRankedCandidatesQuery(
                organization_id=current_user.organization_id,
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
    except ValueError as error:
        _raise_http_error(error)


@router.get("/retrieval-diagnostics", response_model=KnowledgeGraphRetrievalDiagnosticsResponse)
async def get_knowledge_graph_retrieval_diagnostics(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    candidate_direction: str = Query("both"),
    minimum_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    candidate_edge_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphRetrievalDiagnosticsResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphRetrievalDiagnosticsUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphRetrievalDiagnosticsQuery(
                organization_id=current_user.organization_id,
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
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/retrieval-candidates", response_model=KnowledgeGraphRetrievalCandidateResponse)
async def get_knowledge_graph_retrieval_candidates(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    candidate_direction: str = Query("both"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    candidate_edge_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphRetrievalCandidateResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphRetrievalCandidatesUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphRetrievalCandidatesQuery(
                organization_id=current_user.organization_id,
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
    except ValueError as error:
        _raise_http_error(error)


@router.get("/evidence-search", response_model=KnowledgeGraphEvidenceSearchResponse)
async def search_knowledge_graph_evidence(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    result_side: str = Query("source"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphEvidenceSearchResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphEvidenceSearchUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphEvidenceSearchQuery(
                organization_id=current_user.organization_id,
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
    except ValueError as error:
        _raise_http_error(error)


@router.get("/edges", response_model=list[KnowledgeGraphEdgeResponse])
async def list_knowledge_graph_edges(
    source_asset_type: str | None = Query(None),
    source_asset_id: str | None = Query(None),
    target_asset_type: str | None = Query(None),
    target_asset_id: str | None = Query(None),
    relationship_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeGraphEdgeResponse]:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset"),
    )
    try:
        use_case = KnowledgeGraphEdgesListUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphEdgesListQuery(
                organization_id=current_user.organization_id,
                source_asset_type=source_asset_type,
                source_asset_id=source_asset_id,
                target_asset_type=target_asset_type,
                target_asset_id=target_asset_id,
                relationship_type=relationship_type,
                limit=limit,
                offset=offset,
            )
        )
    except ValueError as error:
        _raise_http_error(error)


@router.get("/neighborhood", response_model=KnowledgeGraphNeighborhoodResponse)
async def get_knowledge_graph_neighborhood(
    asset_type: str = Query(...),
    asset_id: str = Query(...),
    direction: str = Query("both"),
    relationship_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphNeighborhoodResponse:
    await require_knowledge_graph_api_access(
        current_user,
        db=db,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "asset", "evidence"),
    )
    try:
        use_case = KnowledgeGraphNeighborhoodUseCase(
            SqlAlchemyKnowledgeGraphAdapter(
                db=db,
            )
        )
        return await use_case.execute(
            KnowledgeGraphNeighborhoodQuery(
                organization_id=current_user.organization_id,
                asset_type=asset_type,
                asset_id=asset_id,
                direction=direction,
                relationship_type=relationship_type,
                limit=limit,
                offset=offset,
            )
        )
    except ValueError as error:
        _raise_http_error(error)
