"""
Unit tests for Control Plane board application service.

Tests board CRUD operations and version history queries in
``app.control_plane.application.board_service.BoardService``.

**Validates: Requirements 9.1**
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.control_plane.application.board_service import BoardService
from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneActiveBoardRecordResponse,
    DeveloperControlPlaneBoardVersionResponse,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight fakes for DB model objects
# ---------------------------------------------------------------------------

def _make_active_board_record(**overrides) -> MagicMock:
    """Build a fake DeveloperControlPlaneActiveBoard row."""
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    defaults = dict(
        id=1,
        organization_id=10,
        board_id="bijmantra-app-development-master-board",
        schema_version="1.2.0",
        visibility="internal-superuser",
        canonical_board_json='{"board_id":"bijmantra-app-development-master-board"}',
        canonical_board_hash="abc123hash",
        updated_by_user_id=42,
        updated_at=now,
        save_source="manual",
        summary_metadata={"lane_count": 3},
        created_at=now,
    )
    defaults.update(overrides)
    record = MagicMock()
    for k, v in defaults.items():
        setattr(record, k, v)
    return record


def _make_board_revision(**overrides) -> MagicMock:
    """Build a fake DeveloperControlPlaneBoardRevision row."""
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    defaults = dict(
        id=5,
        organization_id=10,
        board_id="bijmantra-app-development-master-board",
        schema_version="1.2.0",
        visibility="internal-superuser",
        canonical_board_json='{"board_id":"bijmantra-app-development-master-board"}',
        canonical_board_hash="rev_hash_5",
        saved_by_user_id=42,
        save_source="manual",
        summary_metadata={"lane_count": 2},
        created_at=now,
    )
    defaults.update(overrides)
    revision = MagicMock()
    for k, v in defaults.items():
        setattr(revision, k, v)
    return revision


def _make_user(user_id: int = 42) -> MagicMock:
    """Build a fake User object."""
    user = MagicMock()
    user.id = user_id
    return user


def _make_board_obj(**overrides) -> MagicMock:
    """Build a fake board domain object (duck-typed DeveloperMasterBoard)."""
    defaults = dict(
        board_id="bijmantra-app-development-master-board",
        version="1.2.0",
        visibility="internal-superuser",
    )
    defaults.update(overrides)
    board = MagicMock()
    for k, v in defaults.items():
        setattr(board, k, v)
    return board


# ---------------------------------------------------------------------------
# record_response (static, no DB)
# ---------------------------------------------------------------------------


class TestRecordResponse:
    """Tests for BoardService.record_response — pure mapping."""

    def test_maps_all_fields_correctly(self):
        record = _make_active_board_record()
        resp = BoardService.record_response(record)

        assert isinstance(resp, DeveloperControlPlaneActiveBoardRecordResponse)
        assert resp.id == 1
        assert resp.organization_id == 10
        assert resp.board_id == "bijmantra-app-development-master-board"
        assert resp.schema_version == "1.2.0"
        assert resp.visibility == "internal-superuser"
        assert resp.canonical_board_json == record.canonical_board_json
        assert resp.concurrency_token == "abc123hash"
        assert resp.updated_by_user_id == 42
        assert resp.save_source == "manual"
        assert resp.summary_metadata == {"lane_count": 3}

    def test_concurrency_token_maps_from_canonical_board_hash(self):
        """concurrency_token in the response comes from canonical_board_hash."""
        record = _make_active_board_record(canonical_board_hash="custom_hash_value")
        resp = BoardService.record_response(record)
        assert resp.concurrency_token == "custom_hash_value"

    def test_timestamps_preserved(self):
        ts = datetime(2026, 1, 15, 8, 30, 0, tzinfo=timezone.utc)
        record = _make_active_board_record(created_at=ts, updated_at=ts)
        resp = BoardService.record_response(record)
        assert resp.created_at == ts
        assert resp.updated_at == ts

    def test_none_summary_metadata(self):
        record = _make_active_board_record(summary_metadata=None)
        resp = BoardService.record_response(record)
        assert resp.summary_metadata is None


# ---------------------------------------------------------------------------
# version_response (static, no DB)
# ---------------------------------------------------------------------------


class TestVersionResponse:
    """Tests for BoardService.version_response — pure mapping with is_current."""

    def test_maps_all_fields_correctly(self):
        revision = _make_board_revision(canonical_board_hash="rev_hash_5")
        resp = BoardService.version_response(revision, current_concurrency_token="rev_hash_5")

        assert isinstance(resp, DeveloperControlPlaneBoardVersionResponse)
        assert resp.revision_id == 5
        assert resp.schema_version == "1.2.0"
        assert resp.visibility == "internal-superuser"
        assert resp.concurrency_token == "rev_hash_5"
        assert resp.saved_by_user_id == 42
        assert resp.save_source == "manual"
        assert resp.summary_metadata == {"lane_count": 2}

    def test_is_current_true_when_tokens_match(self):
        revision = _make_board_revision(canonical_board_hash="matching_token")
        resp = BoardService.version_response(revision, current_concurrency_token="matching_token")
        assert resp.is_current is True

    def test_is_current_false_when_tokens_differ(self):
        revision = _make_board_revision(canonical_board_hash="old_token")
        resp = BoardService.version_response(revision, current_concurrency_token="new_token")
        assert resp.is_current is False

    def test_is_current_false_when_current_token_is_none(self):
        revision = _make_board_revision(canonical_board_hash="some_hash")
        resp = BoardService.version_response(revision, current_concurrency_token=None)
        assert resp.is_current is False

    def test_none_summary_metadata(self):
        revision = _make_board_revision(summary_metadata=None)
        resp = BoardService.version_response(revision, current_concurrency_token=None)
        assert resp.summary_metadata is None


# ---------------------------------------------------------------------------
# get_active_board
# ---------------------------------------------------------------------------


class TestGetActiveBoard:
    """Tests for BoardService.get_active_board — async DB query."""

    @pytest.mark.asyncio
    async def test_returns_record_when_found(self):
        record = _make_active_board_record()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_active_board(organization_id=10)

        assert result is record
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_active_board(organization_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_executes_select_query(self):
        """Verify that execute is called with a select statement."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        await service.get_active_board(organization_id=10)

        # execute was called exactly once
        assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# get_board_versions
# ---------------------------------------------------------------------------


class TestGetBoardVersions:
    """Tests for BoardService.get_board_versions — async DB query."""

    @pytest.mark.asyncio
    async def test_returns_list_of_revisions(self):
        rev1 = _make_board_revision(id=1)
        rev2 = _make_board_revision(id=2)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [rev1, rev2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_board_versions(organization_id=10)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] is rev1
        assert result[1] is rev2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_revisions(self):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_board_versions(organization_id=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_executes_single_query(self):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        await service.get_board_versions(organization_id=10)

        assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# get_board_revision
# ---------------------------------------------------------------------------


class TestGetBoardRevision:
    """Tests for BoardService.get_board_revision — async DB query."""

    @pytest.mark.asyncio
    async def test_returns_revision_when_found(self):
        revision = _make_board_revision(id=7)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = revision

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_board_revision(organization_id=10, revision_id=7)

        assert result is revision

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        result = await service.get_board_revision(organization_id=10, revision_id=999)

        assert result is None

    @pytest.mark.asyncio
    async def test_executes_single_query(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        service = BoardService(db)
        await service.get_board_revision(organization_id=10, revision_id=1)

        assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# apply_active_board_state — insert path (current_record is None)
# ---------------------------------------------------------------------------


class TestApplyActiveBoardStateInsert:
    """Tests for apply_active_board_state when current_record is None (insert)."""

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_creates_new_record_and_adds_to_session(self, mock_hash):
        mock_hash.return_value = "new_hash_abc"

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj()
        user = _make_user(user_id=42)

        result = await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=None,
            canonical_board_json='{"board_id":"test"}',
            board=board,
            save_source="manual",
            summary_metadata={"lane_count": 1},
        )

        # A new record was created and added to the session
        assert db.add.call_count >= 1
        first_add_arg = db.add.call_args_list[0][0][0]
        assert first_add_arg.organization_id == 10
        assert first_add_arg.board_id == "bijmantra-app-development-master-board"
        assert first_add_arg.canonical_board_hash == "new_hash_abc"
        assert first_add_arg.updated_by_user_id == 42
        assert first_add_arg.save_source == "manual"

        # flush was called
        db.flush.assert_awaited_once()

        # result is the new record
        assert result is first_add_arg

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_insert_creates_revision_since_hash_differs_from_none(self, mock_hash):
        """When inserting (previous hash is None), a revision is always created."""
        mock_hash.return_value = "brand_new_hash"

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj()
        user = _make_user()

        await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=None,
            canonical_board_json='{"board_id":"test"}',
            board=board,
            save_source="manual",
            summary_metadata={},
        )

        # Two adds: one for the active board, one for the revision
        assert db.add.call_count == 2


# ---------------------------------------------------------------------------
# apply_active_board_state — update path (current_record exists)
# ---------------------------------------------------------------------------


class TestApplyActiveBoardStateUpdate:
    """Tests for apply_active_board_state when current_record exists (update)."""

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_updates_existing_record_fields(self, mock_hash):
        mock_hash.return_value = "updated_hash"

        existing = _make_active_board_record(canonical_board_hash="old_hash")
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj(version="1.2.0", visibility="internal-superuser")
        user = _make_user(user_id=99)

        result = await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=existing,
            canonical_board_json='{"updated":true}',
            board=board,
            save_source="auto-save",
            summary_metadata={"lane_count": 5},
        )

        # The existing record was mutated in place
        assert result is existing
        assert existing.schema_version == "1.2.0"
        assert existing.visibility == "internal-superuser"
        assert existing.canonical_board_json == '{"updated":true}'
        assert existing.canonical_board_hash == "updated_hash"
        assert existing.updated_by_user_id == 99
        assert existing.save_source == "auto-save"
        assert existing.summary_metadata == {"lane_count": 5}

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_creates_revision_when_hash_changes(self, mock_hash):
        mock_hash.return_value = "new_different_hash"

        existing = _make_active_board_record(canonical_board_hash="old_hash")
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj()
        user = _make_user()

        await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=existing,
            canonical_board_json='{"changed":true}',
            board=board,
            save_source="manual",
            summary_metadata={},
        )

        # A revision was added because hash changed
        db.add.assert_called_once()
        revision_arg = db.add.call_args[0][0]
        assert revision_arg.canonical_board_hash == "new_different_hash"
        assert revision_arg.saved_by_user_id == user.id

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_no_revision_when_hash_unchanged(self, mock_hash):
        """When the hash is the same, no revision is created."""
        mock_hash.return_value = "same_hash"

        existing = _make_active_board_record(canonical_board_hash="same_hash")
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj()
        user = _make_user()

        await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=existing,
            canonical_board_json='{"same":true}',
            board=board,
            save_source="manual",
            summary_metadata={},
        )

        # No revision added — db.add should not have been called
        db.add.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.control_plane.application.board_service.hash_canonical_board_json")
    async def test_flush_is_always_called(self, mock_hash):
        """flush is called regardless of whether hash changed."""
        mock_hash.return_value = "same_hash"

        existing = _make_active_board_record(canonical_board_hash="same_hash")
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = BoardService(db)
        board = _make_board_obj()
        user = _make_user()

        await service.apply_active_board_state(
            organization_id=10,
            current_user=user,
            current_record=existing,
            canonical_board_json='{"data":1}',
            board=board,
            save_source="manual",
            summary_metadata={},
        )

        db.flush.assert_awaited_once()
