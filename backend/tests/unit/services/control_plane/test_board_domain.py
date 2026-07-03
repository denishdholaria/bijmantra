"""
Unit tests for Control Plane board domain module.

Tests pure functions and immutable entities in
``app.control_plane.domain.board``.

**Validates: Requirements 8.1**
"""

from __future__ import annotations

import dataclasses
import hashlib
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from app.control_plane.domain.board import (
    BoardEntity,
    BoardVersion,
    build_summary_metadata,
    hash_canonical_board_json,
)


# ---------------------------------------------------------------------------
# hash_canonical_board_json
# ---------------------------------------------------------------------------


class TestHashCanonicalBoardJson:
    """Tests for SHA-256 hash computation of canonical board JSON."""

    def test_produces_correct_sha256_hex_digest(self):
        """Hash output matches hashlib SHA-256 for the same input."""
        payload = '{"board_id": "test", "lanes": []}'
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert hash_canonical_board_json(payload) == expected

    def test_deterministic_same_input_same_output(self):
        """Calling twice with the same input returns the same hash."""
        payload = '{"board_id": "dev-board", "title": "Dev Board"}'
        assert hash_canonical_board_json(payload) == hash_canonical_board_json(payload)

    def test_different_inputs_produce_different_hashes(self):
        """Two distinct inputs must produce distinct hashes."""
        a = '{"board_id": "board-a"}'
        b = '{"board_id": "board-b"}'
        assert hash_canonical_board_json(a) != hash_canonical_board_json(b)

    def test_returns_lowercase_hex_string(self):
        """The digest is a 64-char lowercase hex string."""
        result = hash_canonical_board_json("{}")
        assert len(result) == 64
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_empty_string_hashes_without_error(self):
        """An empty string is a valid input (edge case)."""
        result = hash_canonical_board_json("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected


# ---------------------------------------------------------------------------
# build_summary_metadata
# ---------------------------------------------------------------------------


class TestBuildSummaryMetadata:
    """Tests for summary metadata extraction from a board object."""

    def _make_fake_board(self, **overrides):
        """Create a minimal fake board object for testing."""
        board = MagicMock()
        board.title = overrides.get("title", "Test Board")
        board.visibility = overrides.get("visibility", "internal-superuser")

        lane1 = MagicMock()
        lane1.status = "active"
        lane1.subplans = [MagicMock()]

        lane2 = MagicMock()
        lane2.status = "completed"
        lane2.subplans = [MagicMock(), MagicMock()]

        board.lanes = overrides.get("lanes", [lane1, lane2])

        agent = MagicMock()
        board.agent_roles = overrides.get("agent_roles", [agent])

        cp = MagicMock()
        cp.primary_orchestrator = "OmShriMaatreNamaha"
        board.control_plane = overrides.get("control_plane", cp)

        ac = MagicMock()
        ac.enabled = True
        board.autonomy_contract = overrides.get("autonomy_contract", ac)

        return board

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_returns_expected_structure(self, mock_summary):
        """build_summary_metadata delegates to the schema-layer summary builder."""
        mock_summary.return_value = {
            "title": "Test Board",
            "lane_count": 2,
            "subplan_count": 3,
            "agent_role_count": 1,
            "active_lane_count": 1,
            "visibility": "internal-superuser",
            "primary_orchestrator": "OmShriMaatreNamaha",
            "autonomy_enabled": True,
        }
        board = self._make_fake_board()
        result = build_summary_metadata(board)

        mock_summary.assert_called_once_with(board)
        assert result["title"] == "Test Board"
        assert result["lane_count"] == 2
        assert result["active_lane_count"] == 1
        assert result["autonomy_enabled"] is True

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_merges_extra_metadata(self, mock_summary):
        """Extra metadata keys are merged on top of the base summary."""
        mock_summary.return_value = {"title": "Board", "lane_count": 1}
        board = self._make_fake_board()

        result = build_summary_metadata(
            board, extra_metadata={"restore_source": "v3", "custom_key": 42}
        )

        assert result["title"] == "Board"
        assert result["lane_count"] == 1
        assert result["restore_source"] == "v3"
        assert result["custom_key"] == 42

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_extra_metadata_overrides_base_keys(self, mock_summary):
        """When extra_metadata has a key that collides with the base, extra wins."""
        mock_summary.return_value = {"title": "Original", "lane_count": 5}
        board = self._make_fake_board()

        result = build_summary_metadata(
            board, extra_metadata={"title": "Overridden"}
        )

        assert result["title"] == "Overridden"
        assert result["lane_count"] == 5

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_none_extra_metadata_returns_base_only(self, mock_summary):
        """Passing None for extra_metadata returns the base summary unchanged."""
        base = {"title": "Board", "lane_count": 2}
        mock_summary.return_value = base.copy()
        board = self._make_fake_board()

        result = build_summary_metadata(board, extra_metadata=None)
        assert result == base


# ---------------------------------------------------------------------------
# BoardEntity
# ---------------------------------------------------------------------------


class TestBoardEntity:
    """Tests for the immutable BoardEntity dataclass."""

    def _make_entity(self, **overrides):
        defaults = dict(
            board_id="dev-board",
            title="Dev Board",
            canonical_json='{"board_id":"dev-board"}',
            concurrency_token="abc123",
            schema_version="1.2.0",
            visibility="internal-superuser",
            lane_count=3,
            summary_metadata={"title": "Dev Board"},
        )
        defaults.update(overrides)
        return BoardEntity(**defaults)

    def test_frozen_immutable(self):
        """BoardEntity is frozen — attribute assignment raises."""
        entity = self._make_entity()
        with pytest.raises(dataclasses.FrozenInstanceError):
            entity.board_id = "changed"

    def test_frozen_immutable_title(self):
        """Cannot mutate the title field."""
        entity = self._make_entity()
        with pytest.raises(dataclasses.FrozenInstanceError):
            entity.title = "new title"

    def test_default_lane_count_is_zero(self):
        """lane_count defaults to 0 when not provided."""
        entity = BoardEntity(
            board_id="b",
            title="t",
            canonical_json="{}",
            concurrency_token="tok",
            schema_version="1.0.0",
            visibility="internal-superuser",
        )
        assert entity.lane_count == 0

    def test_default_summary_metadata_is_empty_dict(self):
        """summary_metadata defaults to an empty dict."""
        entity = BoardEntity(
            board_id="b",
            title="t",
            canonical_json="{}",
            concurrency_token="tok",
            schema_version="1.0.0",
            visibility="internal-superuser",
        )
        assert entity.summary_metadata == {}

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_from_board_factory(self, mock_summary):
        """from_board constructs a BoardEntity from a board object."""
        mock_summary.return_value = {"title": "My Board", "lane_count": 2}

        board = MagicMock()
        board.board_id = "my-board"
        board.title = "My Board"
        board.visibility = "internal-superuser"
        board.lanes = [MagicMock(), MagicMock()]

        canonical = '{"board_id":"my-board"}'
        entity = BoardEntity.from_board(board, canonical, "1.2.0")

        assert entity.board_id == "my-board"
        assert entity.title == "My Board"
        assert entity.canonical_json == canonical
        assert entity.concurrency_token == hash_canonical_board_json(canonical)
        assert entity.schema_version == "1.2.0"
        assert entity.visibility == "internal-superuser"
        assert entity.lane_count == 2
        assert entity.summary_metadata == {"title": "My Board", "lane_count": 2}

    @patch(
        "app.schemas.developer_control_plane.build_developer_master_board_summary",
    )
    def test_from_board_no_lanes_attribute(self, mock_summary):
        """from_board handles a board object without a lanes attribute."""
        mock_summary.return_value = {"title": "Bare Board"}

        board = MagicMock(spec=[])  # no attributes by default
        board.board_id = "bare"
        board.title = "Bare Board"
        board.visibility = "internal-superuser"
        # deliberately no board.lanes

        entity = BoardEntity.from_board(board, "{}", "1.0.0")
        assert entity.lane_count == 0


# ---------------------------------------------------------------------------
# BoardVersion
# ---------------------------------------------------------------------------


class TestBoardVersion:
    """Tests for the immutable BoardVersion dataclass."""

    def _make_version(self, **overrides):
        defaults = dict(
            revision_id=1,
            schema_version="1.2.0",
            visibility="internal-superuser",
            concurrency_token="deadbeef",
            created_at=datetime(2026, 4, 15, 12, 0, 0),
            saved_by_user_id=42,
            save_source="manual",
            summary_metadata={"lane_count": 5},
            is_current=False,
        )
        defaults.update(overrides)
        return BoardVersion(**defaults)

    def test_frozen_immutable(self):
        """BoardVersion is frozen — attribute assignment raises."""
        version = self._make_version()
        with pytest.raises(dataclasses.FrozenInstanceError):
            version.revision_id = 99

    def test_frozen_immutable_save_source(self):
        """Cannot mutate the save_source field."""
        version = self._make_version()
        with pytest.raises(dataclasses.FrozenInstanceError):
            version.save_source = "auto"

    def test_default_summary_metadata_is_empty_dict(self):
        """summary_metadata defaults to an empty dict."""
        version = BoardVersion(
            revision_id=1,
            schema_version="1.0.0",
            visibility="internal-superuser",
            concurrency_token="tok",
            created_at=datetime(2026, 1, 1),
            saved_by_user_id=1,
            save_source="manual",
        )
        assert version.summary_metadata == {}

    def test_default_is_current_is_false(self):
        """is_current defaults to False."""
        version = BoardVersion(
            revision_id=1,
            schema_version="1.0.0",
            visibility="internal-superuser",
            concurrency_token="tok",
            created_at=datetime(2026, 1, 1),
            saved_by_user_id=1,
            save_source="manual",
        )
        assert version.is_current is False

    def test_all_fields_accessible(self):
        """All fields are readable after construction."""
        version = self._make_version(is_current=True)
        assert version.revision_id == 1
        assert version.schema_version == "1.2.0"
        assert version.visibility == "internal-superuser"
        assert version.concurrency_token == "deadbeef"
        assert version.created_at == datetime(2026, 4, 15, 12, 0, 0)
        assert version.saved_by_user_id == 42
        assert version.save_source == "manual"
        assert version.summary_metadata == {"lane_count": 5}
        assert version.is_current is True
