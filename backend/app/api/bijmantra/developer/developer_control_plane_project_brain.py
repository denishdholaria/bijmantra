"""Hidden developer-control-plane API for project-brain sidecar queries."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_superuser
from app.modules.ai.services import (
    ProjectBrainMemoryService,
    ProjectBrainQueryService,
    ProjectBrainScope,
    ProjectBrainSurrealConnectionConfig,
    ProjectBrainSurrealRepositoryError,
    ProjectBrainTrustRank,
    SurrealProjectBrainMemoryRepository,
)


router = APIRouter(
    prefix="/developer-control-plane/project-brain",
    tags=["Developer Control Plane"],
    dependencies=[Depends(get_current_superuser)],
)


@dataclass(frozen=True, slots=True)
class ProjectBrainQueryRuntime:
    config: ProjectBrainSurrealConnectionConfig
    query_service: ProjectBrainQueryService


class ProjectBrainQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=240)
    include_provenance: bool = False
    trust_ranks: list[ProjectBrainTrustRank] | None = None
    scopes: list[ProjectBrainScope] | None = None


class ProjectBrainSidecarResponse(BaseModel):
    base_url: str
    namespace: str
    database: str
    is_optional: bool = True
    is_non_authoritative: bool = True


class ProjectBrainQueryResponse(BaseModel):
    query: str
    sidecar: ProjectBrainSidecarResponse
    recall_view: dict[str, Any]
    provenance_trails: list[dict[str, Any]] = Field(default_factory=list)


def _project_brain_sidecar_unavailable_detail(
    config: ProjectBrainSurrealConnectionConfig,
    *,
    reason: str | None = None,
) -> str:
    detail = (
        f"Being Bijmantra project-brain sidecar is unavailable at {config.base_url}. "
        "Start it with make dev-beingbijmantra, then bootstrap the schema and first-wave project-brain data before querying."
    )
    if reason:
        return f"{detail} Reason: {reason}"
    return detail


async def get_project_brain_query_runtime() -> AsyncIterator[ProjectBrainQueryRuntime]:
    config = ProjectBrainSurrealConnectionConfig()
    repository = SurrealProjectBrainMemoryRepository(config)
    try:
        await repository.check_health()
        query_service = ProjectBrainQueryService(ProjectBrainMemoryService(repository))
        yield ProjectBrainQueryRuntime(config=config, query_service=query_service)
    except (httpx.HTTPError, ProjectBrainSurrealRepositoryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_project_brain_sidecar_unavailable_detail(config, reason=str(exc)),
        ) from exc
    finally:
        await repository.aclose()


@router.post("/query", response_model=ProjectBrainQueryResponse)
async def query_project_brain(
    payload: ProjectBrainQueryRequest,
    runtime: ProjectBrainQueryRuntime = Depends(get_project_brain_query_runtime),
) -> ProjectBrainQueryResponse:
    try:
        result = await runtime.query_service.query(
            payload.query,
            include_provenance=payload.include_provenance,
            trust_ranks=tuple(payload.trust_ranks) if payload.trust_ranks else None,
            scopes=tuple(payload.scopes) if payload.scopes else None,
        )
    except (httpx.HTTPError, ProjectBrainSurrealRepositoryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_project_brain_sidecar_unavailable_detail(runtime.config, reason=str(exc)),
        ) from exc

    return ProjectBrainQueryResponse(
        query=result.query,
        sidecar=ProjectBrainSidecarResponse(
            base_url=runtime.config.base_url,
            namespace=runtime.config.namespace,
            database=runtime.config.database,
        ),
        recall_view=result.recall_view.to_dict(),
        provenance_trails=[item.to_dict() for item in result.provenance_trails],
    )