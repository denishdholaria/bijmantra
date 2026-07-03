"""Pure mission domain functions and entities for the Control Plane.

All functions and classes in this module are infrastructure-free: no database,
filesystem, or HTTP imports.  This module encapsulates mission state, source
request parsing, and lane/job/board token linkage resolution.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MISSION_LINKAGE_SOURCE_REQUEST_PATTERN = re.compile(
    r"^Developer control-plane "
    r"(?P<event>explicit completion write-back|stable closeout receipt observed) for lane "
    r"(?P<lane_id>[^ ]+) from queue job (?P<queue_job_id>[^.]+)\."
    r"(?: Context: source_board_concurrency_token=(?P<board_token>[^.]+)\.)?$"
)


# ---------------------------------------------------------------------------
# Pure functions — extracted from developer_control_plane.py
# ---------------------------------------------------------------------------


def parse_completion_source_request(
    source_request: str | None,
) -> dict[str, str | None] | None:
    """Parse a mission ``source_request`` string to extract lane/job linkage.

    The source request string follows a structured format produced by the
    control plane when recording mission state.  This function extracts the
    ``source_lane_id``, ``queue_job_id``, and (optionally)
    ``source_board_concurrency_token`` from that string.

    Parameters
    ----------
    source_request:
        The raw source request string, or ``None``.

    Returns
    -------
    dict[str, str | None] | None
        A dict with keys ``source_lane_id``, ``queue_job_id``, and
        ``source_board_concurrency_token``, or ``None`` if the string
        is empty or does not match the expected pattern.
    """
    if not source_request:
        return None

    match = MISSION_LINKAGE_SOURCE_REQUEST_PATTERN.match(source_request.strip())
    if match is None:
        return None

    return {
        "source_lane_id": match.group("lane_id"),
        "queue_job_id": match.group("queue_job_id"),
        "source_board_concurrency_token": match.group("board_token"),
    }


def mission_linkage(mission: Any) -> dict[str, str | None] | None:
    """Resolve the lane/job/board-token linkage for a mission object.

    Checks the mission's direct columns (``queue_job_id``,
    ``source_lane_id``, ``source_board_concurrency_token``) first.  If
    none of them are populated, falls back to parsing the
    ``source_request`` string via :func:`parse_completion_source_request`.

    Parameters
    ----------
    mission:
        A mission object (or duck-typed equivalent) with attributes
        ``queue_job_id``, ``source_lane_id``,
        ``source_board_concurrency_token``, and ``source_request``.

    Returns
    -------
    dict[str, str | None] | None
        A dict with keys ``queue_job_id``, ``source_lane_id``, and
        ``source_board_concurrency_token``, or ``None`` if no linkage
        can be resolved.
    """
    queue_job_id = mission.queue_job_id if isinstance(mission.queue_job_id, str) else None
    source_lane_id = mission.source_lane_id if isinstance(mission.source_lane_id, str) else None
    source_board_concurrency_token = (
        mission.source_board_concurrency_token
        if isinstance(mission.source_board_concurrency_token, str)
        else None
    )

    if (
        queue_job_id is not None
        or source_lane_id is not None
        or source_board_concurrency_token is not None
    ):
        return {
            "queue_job_id": queue_job_id,
            "source_lane_id": source_lane_id,
            "source_board_concurrency_token": source_board_concurrency_token,
        }

    return parse_completion_source_request(mission.source_request)


# ---------------------------------------------------------------------------
# Domain entities — immutable mission state containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissionLinkage:
    """Immutable linkage between a mission and its source lane/job/board.

    Captures the provenance chain from a mission back to the board lane
    and queue job that originated it.

    Attributes
    ----------
    queue_job_id : str | None
        The queue job identifier that spawned this mission.
    source_lane_id : str | None
        The board lane identifier that the mission is linked to.
    source_board_concurrency_token : str | None
        The board concurrency token at the time the mission was created.
    """

    queue_job_id: str | None = None
    source_lane_id: str | None = None
    source_board_concurrency_token: str | None = None

    @property
    def is_resolved(self) -> bool:
        """Whether at least one linkage field is populated."""
        return (
            self.queue_job_id is not None
            or self.source_lane_id is not None
            or self.source_board_concurrency_token is not None
        )

    def to_dict(self) -> dict[str, str | None]:
        """Serialize to the dict format used by the API layer."""
        return {
            "queue_job_id": self.queue_job_id,
            "source_lane_id": self.source_lane_id,
            "source_board_concurrency_token": self.source_board_concurrency_token,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> MissionLinkage:
        """Construct a :class:`MissionLinkage` from a dict."""
        return cls(
            queue_job_id=data.get("queue_job_id"),
            source_lane_id=data.get("source_lane_id"),
            source_board_concurrency_token=data.get("source_board_concurrency_token"),
        )

    @classmethod
    def from_mission(cls, mission: Any) -> MissionLinkage | None:
        """Construct a :class:`MissionLinkage` from a mission object.

        Delegates to :func:`mission_linkage` and wraps the result.
        Returns ``None`` if no linkage can be resolved.
        """
        linkage_dict = mission_linkage(mission)
        if linkage_dict is None:
            return None
        return cls.from_dict(linkage_dict)


@dataclass(frozen=True)
class MissionEntity:
    """Immutable snapshot of a mission's state.

    This is a domain-layer value object that captures the essential
    identity and provenance of a mission without any persistence
    concerns.

    Attributes
    ----------
    mission_id : str
        The unique mission identifier.
    objective : str
        Human-readable mission objective.
    owner : str
        The agent role that owns this mission (e.g. ``"OmShriMaatreNamaha"``).
    priority : str
        Mission priority (e.g. ``"p1"``, ``"p2"``).
    status : str
        Current mission status (e.g. ``"active"``, ``"completed"``).
    linkage : MissionLinkage | None
        Resolved linkage to source lane/job/board, or ``None``.
    producer_key : str
        The producer key identifying the origin of this mission.
    source_request : str
        The structured source request string.
    verification_passed : int
        Count of verification runs that passed.
    verification_warned : int
        Count of verification runs that warned.
    verification_failed : int
        Count of verification runs that failed.
    blocker_count : int
        Number of active blockers on this mission.
    subtask_count : int
        Total number of subtasks.
    subtask_completed : int
        Number of completed subtasks.
    evidence_count : int
        Number of evidence items attached.
    decision_count : int
        Number of decision notes recorded.
    """

    mission_id: str
    objective: str = ""
    owner: str = ""
    priority: str = "p2"
    status: str = "active"
    linkage: MissionLinkage | None = None
    producer_key: str = "developer-control-plane"
    source_request: str = ""
    verification_passed: int = 0
    verification_warned: int = 0
    verification_failed: int = 0
    blocker_count: int = 0
    subtask_count: int = 0
    subtask_completed: int = 0
    evidence_count: int = 0
    decision_count: int = 0
