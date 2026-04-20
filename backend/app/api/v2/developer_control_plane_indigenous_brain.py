"""Hidden developer-control-plane Indigenous Brain world-model API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.core.database import get_db
from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneLearningEntry,
)
from app.models.orchestrator_state import OrchestratorMission
from app.modules.ai.services.developer_control_plane_indigenous_brain import (
    DEFAULT_PROJECT_BRAIN_QUERY,
    build_developer_control_plane_indigenous_brain_brief,
)
from app.modules.ai.services.project_brain_memory import ProjectBrainMemoryService
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    ProjectBrainSurrealRepositoryError,
    SurrealProjectBrainMemoryRepository,
)
from app.modules.ai.services.project_brain_query import ProjectBrainQueryService
from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_ID


REPO_ROOT = Path(__file__).resolve().parents[4]
OVERNIGHT_QUEUE_PATH = REPO_ROOT / ".agent" / "jobs" / "overnight-queue.json"


router = APIRouter(
    prefix="/developer-control-plane/indigenous-brain",
    tags=["Developer Control Plane"],
    dependencies=[Depends(get_current_superuser)],
)


@dataclass(frozen=True, slots=True)
class OptionalProjectBrainQueryRuntime:
    base_url: str
    query_service: ProjectBrainQueryService | None
    detail: str | None = None


async def get_optional_project_brain_query_runtime() -> AsyncIterator[OptionalProjectBrainQueryRuntime]:
    config = ProjectBrainSurrealConnectionConfig()
    repository = SurrealProjectBrainMemoryRepository(config)
    try:
        await repository.check_health()
        yield OptionalProjectBrainQueryRuntime(
            base_url=config.base_url,
            query_service=ProjectBrainQueryService(ProjectBrainMemoryService(repository)),
            detail=None,
        )
    except (httpx.HTTPError, ProjectBrainSurrealRepositoryError) as exc:
        yield OptionalProjectBrainQueryRuntime(
            base_url=config.base_url,
            query_service=None,
            detail=(
                f"Project-brain sidecar is unavailable at {config.base_url}. "
                "Start it with make dev-beingbijmantra before requesting enriched recall. "
                f"Reason: {exc}"
            ),
        )
    finally:
        await repository.aclose()


async def _load_active_board_record(
    db: AsyncSession,
    organization_id: int,
) -> tuple[DeveloperControlPlaneActiveBoard | None, str | None]:
    try:
        result = await db.execute(
            select(DeveloperControlPlaneActiveBoard).where(
                DeveloperControlPlaneActiveBoard.organization_id == organization_id,
                DeveloperControlPlaneActiveBoard.board_id == DEVELOPER_MASTER_BOARD_ID,
            )
        )
    except SQLAlchemyError as exc:
        return None, f"Active-board surface unavailable: {exc.__class__.__name__}"

    return result.scalar_one_or_none(), None


async def _load_recent_missions(
    db: AsyncSession,
    organization_id: int,
) -> tuple[list[OrchestratorMission], int, str | None]:
    try:
        total_count = int(
            await db.scalar(
                select(func.count()).select_from(OrchestratorMission).where(
                    OrchestratorMission.organization_id == organization_id
                )
            )
            or 0
        )
        result = await db.execute(
            select(OrchestratorMission)
            .where(OrchestratorMission.organization_id == organization_id)
            .order_by(OrchestratorMission.updated_at.desc())
            .limit(6)
        )
    except SQLAlchemyError as exc:
        return [], 0, f"Mission-state surface unavailable: {exc.__class__.__name__}"

    return list(result.scalars()), total_count, None


async def _load_recent_learnings(
    db: AsyncSession,
    organization_id: int,
) -> tuple[list[DeveloperControlPlaneLearningEntry], int, str | None]:
    try:
        total_count = int(
            await db.scalar(
                select(func.count()).select_from(DeveloperControlPlaneLearningEntry).where(
                    DeveloperControlPlaneLearningEntry.organization_id == organization_id
                )
            )
            or 0
        )
        result = await db.execute(
            select(DeveloperControlPlaneLearningEntry)
            .where(DeveloperControlPlaneLearningEntry.organization_id == organization_id)
            .order_by(DeveloperControlPlaneLearningEntry.created_at.desc())
            .limit(6)
        )
    except SQLAlchemyError as exc:
        return [], 0, f"Learning-ledger surface unavailable: {exc.__class__.__name__}"

    return list(result.scalars()), total_count, None


@router.get("/brief")
async def get_indigenous_brain_brief(
    project_brain_query: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    project_brain_runtime: OptionalProjectBrainQueryRuntime = Depends(
        get_optional_project_brain_query_runtime
    ),
):
    normalized_project_brain_query = (
        project_brain_query.strip()
        if project_brain_query and project_brain_query.strip()
        else DEFAULT_PROJECT_BRAIN_QUERY
    )
    active_board_record, board_error = await _load_active_board_record(db, organization_id)
    mission_records, mission_total_count, mission_error = await _load_recent_missions(
        db,
        organization_id,
    )
    learning_entries, learning_total_count, learning_error = await _load_recent_learnings(
        db,
        organization_id,
    )

    return await build_developer_control_plane_indigenous_brain_brief(
        active_board_record=active_board_record,
        board_error=board_error,
        mission_records=mission_records,
        mission_total_count=mission_total_count,
        mission_error=mission_error,
        learning_entries=learning_entries,
        learning_total_count=learning_total_count,
        learning_error=learning_error,
        queue_path=OVERNIGHT_QUEUE_PATH,
        project_brain_query_service=project_brain_runtime.query_service,
        project_brain_base_url=project_brain_runtime.base_url,
        project_brain_query=normalized_project_brain_query,
        project_brain_detail=project_brain_runtime.detail,
    )