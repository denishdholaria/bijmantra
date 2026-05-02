"""Board application service — CRUD operations with database persistence.

This module is the application-layer home for board read/write operations
that require infrastructure (SQLAlchemy ``AsyncSession``).  It bridges the
pure domain layer (``control_plane.domain.board``) and the persistence
models (``app.models.developer_control_plane``).

Extracted from ``backend/app/api/v2/developer_control_plane.py``.

Requirements: 9.1, 9.5, 9.6
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneActiveBoardRecordResponse,
    DeveloperControlPlaneBoardVersionResponse,
)
from app.control_plane.domain.board import hash_canonical_board_json
from app.models.core import User
from app.models.developer_control_plane import (
    DeveloperControlPlaneActiveBoard,
    DeveloperControlPlaneBoardRevision,
)
from app.schemas.developer_control_plane import DEVELOPER_MASTER_BOARD_ID


class BoardService:
    """Application service for board CRUD operations.

    Accepts an ``AsyncSession`` as a constructor dependency so that
    callers control transaction boundaries.

    All public methods mirror the exact behavior of the private helpers
    previously inlined in ``developer_control_plane.py``.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_active_board(
        self,
        organization_id: int,
    ) -> DeveloperControlPlaneActiveBoard | None:
        """Fetch the current active board for *organization_id*.

        Returns ``None`` when no board has been persisted yet.
        """
        result = await self._db.execute(
            select(DeveloperControlPlaneActiveBoard).where(
                DeveloperControlPlaneActiveBoard.organization_id == organization_id,
                DeveloperControlPlaneActiveBoard.board_id == DEVELOPER_MASTER_BOARD_ID,
            )
        )
        return result.scalar_one_or_none()

    async def get_board_versions(
        self,
        organization_id: int,
    ) -> list[DeveloperControlPlaneBoardRevision]:
        """Return all board revisions for *organization_id*, newest first."""
        result = await self._db.execute(
            select(DeveloperControlPlaneBoardRevision)
            .where(
                DeveloperControlPlaneBoardRevision.organization_id == organization_id,
                DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
            )
            .order_by(
                DeveloperControlPlaneBoardRevision.created_at.desc(),
                DeveloperControlPlaneBoardRevision.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def get_board_revision(
        self,
        organization_id: int,
        revision_id: int,
    ) -> DeveloperControlPlaneBoardRevision | None:
        """Fetch a single board revision by *revision_id*."""
        result = await self._db.execute(
            select(DeveloperControlPlaneBoardRevision).where(
                DeveloperControlPlaneBoardRevision.id == revision_id,
                DeveloperControlPlaneBoardRevision.organization_id == organization_id,
                DeveloperControlPlaneBoardRevision.board_id == DEVELOPER_MASTER_BOARD_ID,
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def apply_active_board_state(
        self,
        organization_id: int,
        current_user: User,
        current_record: DeveloperControlPlaneActiveBoard | None,
        *,
        canonical_board_json: str,
        board: Any,
        save_source: str,
        summary_metadata: dict[str, Any],
    ) -> DeveloperControlPlaneActiveBoard:
        """Persist a new board state snapshot.

        If *current_record* is ``None`` a new row is inserted; otherwise
        the existing row is updated in place.  When the board hash
        changes a new ``DeveloperControlPlaneBoardRevision`` is also
        created.

        The caller is responsible for committing the transaction.
        """
        previous_board_hash = (
            current_record.canonical_board_hash if current_record is not None else None
        )
        board_hash = hash_canonical_board_json(canonical_board_json)

        if current_record is None:
            current_record = DeveloperControlPlaneActiveBoard(
                organization_id=organization_id,
                board_id=board.board_id,
                schema_version=board.version,
                visibility=board.visibility,
                canonical_board_json=canonical_board_json,
                canonical_board_hash=board_hash,
                updated_by_user_id=current_user.id,
                save_source=save_source,
                summary_metadata=summary_metadata,
            )
            self._db.add(current_record)
        else:
            current_record.schema_version = board.version
            current_record.visibility = board.visibility
            current_record.canonical_board_json = canonical_board_json
            current_record.canonical_board_hash = board_hash
            current_record.updated_by_user_id = current_user.id
            current_record.save_source = save_source
            current_record.summary_metadata = summary_metadata

        await self._db.flush()

        if previous_board_hash != board_hash:
            self._db.add(
                DeveloperControlPlaneBoardRevision(
                    organization_id=organization_id,
                    board_id=board.board_id,
                    schema_version=board.version,
                    visibility=board.visibility,
                    canonical_board_json=canonical_board_json,
                    canonical_board_hash=board_hash,
                    saved_by_user_id=current_user.id,
                    save_source=save_source,
                    summary_metadata=summary_metadata,
                )
            )

        return current_record

    # ------------------------------------------------------------------
    # Response builders
    # ------------------------------------------------------------------

    @staticmethod
    def record_response(
        record: DeveloperControlPlaneActiveBoard,
    ) -> DeveloperControlPlaneActiveBoardRecordResponse:
        """Build an API response model from a persisted board record.

        This is a pure mapping with no side effects.
        """
        return DeveloperControlPlaneActiveBoardRecordResponse(
            id=record.id,
            organization_id=record.organization_id,
            board_id=record.board_id,
            schema_version=record.schema_version,
            visibility=record.visibility,
            canonical_board_json=record.canonical_board_json,
            concurrency_token=record.canonical_board_hash,
            updated_by_user_id=record.updated_by_user_id,
            updated_at=record.updated_at,
            save_source=record.save_source,
            summary_metadata=record.summary_metadata,
            created_at=record.created_at,
        )

    @staticmethod
    def version_response(
        record: DeveloperControlPlaneBoardRevision,
        current_concurrency_token: str | None,
    ) -> DeveloperControlPlaneBoardVersionResponse:
        """Build an API response model from a board revision record."""
        return DeveloperControlPlaneBoardVersionResponse(
            revision_id=record.id,
            schema_version=record.schema_version,
            visibility=record.visibility,
            concurrency_token=record.canonical_board_hash,
            created_at=record.created_at,
            saved_by_user_id=record.saved_by_user_id,
            save_source=record.save_source,
            summary_metadata=record.summary_metadata,
            is_current=current_concurrency_token == record.canonical_board_hash,
        )
