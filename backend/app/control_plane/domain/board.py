"""Pure board domain functions and entities for the Control Plane.

All functions and classes in this module are infrastructure-free: no database,
filesystem, or HTTP imports.  This module encapsulates board state, version
management, and lane containment logic.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Pure functions — extracted from developer_control_plane.py
# ---------------------------------------------------------------------------


def hash_canonical_board_json(canonical_board_json: str) -> str:
    """Compute the SHA-256 hash of a canonical board JSON string.

    This hash serves as the concurrency token (optimistic lock) for board
    state.  The input **must** be the canonical (deterministic) JSON
    representation produced by ``canonicalize_developer_master_board_json``.

    Returns a lowercase hex digest string.
    """
    return hashlib.sha256(canonical_board_json.encode("utf-8")).hexdigest()


def build_summary_metadata(
    board: Any,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build summary metadata for a board state snapshot.

    Delegates to :func:`build_developer_master_board_summary` from the
    schema layer for the core summary fields, then merges any
    *extra_metadata* (e.g. restore context, completion evidence) on top.

    Parameters
    ----------
    board:
        A validated ``DeveloperMasterBoard`` instance (or duck-typed
        equivalent with the same attributes).
    extra_metadata:
        Optional dict of additional metadata to merge into the summary.

    Returns
    -------
    dict[str, Any]
        The merged summary metadata dict.
    """
    from app.schemas.developer_control_plane import (
        build_developer_master_board_summary,
    )

    summary_metadata = build_developer_master_board_summary(board)
    if extra_metadata is not None:
        summary_metadata = {**summary_metadata, **extra_metadata}
    return summary_metadata


# ---------------------------------------------------------------------------
# Domain entities — immutable board state containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BoardEntity:
    """Immutable snapshot of a board's canonical state.

    This is a domain-layer value object that captures the essential
    identity and content of a board without any persistence concerns.

    Attributes
    ----------
    board_id : str
        The unique board identifier (e.g. ``"developer-master-board"``).
    title : str
        Human-readable board title.
    canonical_json : str
        The deterministic JSON representation of the board.
    concurrency_token : str
        SHA-256 hash of *canonical_json*, used for optimistic locking.
    schema_version : str
        The board schema version string.
    visibility : str
        Board visibility level (e.g. ``"internal-superuser"``).
    lane_count : int
        Number of lanes in the board.
    summary_metadata : dict[str, Any]
        Pre-computed summary metadata for the board snapshot.
    """

    board_id: str
    title: str
    canonical_json: str
    concurrency_token: str
    schema_version: str
    visibility: str
    lane_count: int = 0
    summary_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_board(
        cls,
        board: Any,
        canonical_json: str,
        schema_version: str,
    ) -> BoardEntity:
        """Construct a :class:`BoardEntity` from a validated board object.

        Parameters
        ----------
        board:
            A validated ``DeveloperMasterBoard`` instance.
        canonical_json:
            The canonical JSON string for the board.
        schema_version:
            The schema version string.
        """
        return cls(
            board_id=board.board_id,
            title=board.title,
            canonical_json=canonical_json,
            concurrency_token=hash_canonical_board_json(canonical_json),
            schema_version=schema_version,
            visibility=board.visibility,
            lane_count=len(board.lanes) if hasattr(board, "lanes") else 0,
            summary_metadata=build_summary_metadata(board),
        )


@dataclass(frozen=True)
class BoardVersion:
    """Immutable version metadata for a board revision.

    Captures the identity and provenance of a single board revision
    in the version history, without carrying the full board content.

    Attributes
    ----------
    revision_id : int
        The database-assigned revision identifier.
    schema_version : str
        The board schema version at the time of this revision.
    visibility : str
        Board visibility level at the time of this revision.
    concurrency_token : str
        SHA-256 hash of the canonical board JSON for this revision.
    created_at : datetime
        Timestamp when this revision was persisted.
    saved_by_user_id : int
        The user who triggered the save.
    save_source : str
        The source of the save action (e.g. ``"manual"``, ``"restore-version"``).
    summary_metadata : dict[str, Any]
        Pre-computed summary metadata for this revision.
    is_current : bool
        Whether this revision matches the currently active board state.
    """

    revision_id: int
    schema_version: str
    visibility: str
    concurrency_token: str
    created_at: datetime
    saved_by_user_id: int
    save_source: str
    summary_metadata: dict[str, Any] = field(default_factory=dict)
    is_current: bool = False
