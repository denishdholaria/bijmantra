"""Queue materializer orchestrator for the Control Plane.

Derives queue jobs from board lanes, computes SHA256 hashes for optimistic
locking, and manages the overnight queue filesystem artifact.  This module
is part of the orchestration layer and **may** use infrastructure imports
(filesystem, JSON I/O) — that is expected for queue materialization.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.control_plane.contracts.api_schema import (
    DeveloperControlPlaneOvernightQueueStatusResponse,
)
from app.control_plane.domain.validation import (
    QUEUE_LANGUAGE,
    QUEUE_VOCABULARY_POLICY,
    DomainValidationError,
    validate_queue_payload_shape,
)
from app.services.control_plane import telemetry_service


# ---------------------------------------------------------------------------
# Path resolution — mirrors the constants in developer_control_plane.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[5]
_OVERNIGHT_QUEUE_PATH = _REPO_ROOT / ".agent" / "jobs" / "overnight-queue.json"


# ---------------------------------------------------------------------------
# QueueMaterializer — orchestrator class
# ---------------------------------------------------------------------------


class QueueMaterializer:
    """Orchestrator for overnight-queue derivation and persistence.

    All methods are intentionally ``@staticmethod`` so that the class acts
    as a namespace grouping related queue operations.  Infrastructure
    dependencies (filesystem paths) are resolved at module level.
    """

    # ------------------------------------------------------------------
    # Queue payload defaults
    # ------------------------------------------------------------------

    @staticmethod
    def default_queue_payload() -> dict[str, Any]:
        """Return the default empty queue payload structure.

        This is the canonical shape of a fresh overnight queue with no
        jobs.  Used as a fallback when the queue file does not exist or
        is malformed.
        """
        return {
            "version": 1,
            "updatedAt": None,
            "language": QUEUE_LANGUAGE,
            "vocabularyPolicy": QUEUE_VOCABULARY_POLICY,
            "defaults": {
                "window": "nightly",
                "stateRefreshRequired": True,
                "closeoutCommands": ["make update-state"],
                "maxJobsPerRun": 2,
            },
            "jobs": [],
        }

    # ------------------------------------------------------------------
    # SHA256 computation
    # ------------------------------------------------------------------

    @staticmethod
    def queue_sha256(payload: dict[str, Any]) -> str:
        """Compute the SHA-256 hash of a queue payload.

        The payload is serialized with sorted keys and compact separators
        to produce a deterministic digest suitable for optimistic locking.
        """
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Queue loading (filesystem)
    # ------------------------------------------------------------------

    @staticmethod
    def load_overnight_queue_payload() -> tuple[dict[str, Any], bool]:
        """Load the overnight queue payload from the filesystem.

        Returns
        -------
        tuple[dict, bool]
            A 2-tuple of ``(payload, exists)``.  When the file is missing
            or malformed the default payload is returned with
            ``exists=False``.
        """
        if not _OVERNIGHT_QUEUE_PATH.exists():
            return QueueMaterializer.default_queue_payload(), False

        try:
            payload = json.loads(
                _OVERNIGHT_QUEUE_PATH.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            malformed = QueueMaterializer.default_queue_payload()
            malformed["malformed_artifact"] = True
            malformed["error"] = str(exc)
            return malformed, False

        if not isinstance(payload, dict):
            malformed = QueueMaterializer.default_queue_payload()
            malformed["malformed_artifact"] = True
            malformed["error"] = "Overnight queue payload must be a JSON object"
            return malformed, False

        return payload, True

    # ------------------------------------------------------------------
    # Queue serialization and writing (filesystem)
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_queue_payload(payload: dict[str, Any]) -> str:
        """Serialize a queue payload to a stable JSON string.

        The output uses a fixed key order so that the serialized form is
        deterministic across writes.
        """
        stable_payload = {
            "version": payload.get("version", 1),
            "updatedAt": payload.get("updatedAt"),
            "language": payload.get("language", QUEUE_LANGUAGE),
            "vocabularyPolicy": payload.get(
                "vocabularyPolicy", QUEUE_VOCABULARY_POLICY
            ),
            "defaults": payload.get(
                "defaults",
                QueueMaterializer.default_queue_payload()["defaults"],
            ),
            "jobs": payload.get("jobs", []),
        }
        return f"{json.dumps(stable_payload, indent=2, ensure_ascii=True)}\n"

    @staticmethod
    def write_overnight_queue_payload(payload: dict[str, Any]) -> None:
        """Write the overnight queue payload to the filesystem.

        Creates parent directories if they do not exist.

        Raises
        ------
        OSError
            If the file cannot be written.  The caller (API layer) is
            responsible for translating this into an HTTP 500 response.
        """
        _OVERNIGHT_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _OVERNIGHT_QUEUE_PATH.write_text(
            QueueMaterializer.serialize_queue_payload(payload),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Job ID creation and lookup
    # ------------------------------------------------------------------

    @staticmethod
    def _queue_token_suffix(source_board_concurrency_token: str) -> str:
        """Derive a short alphanumeric suffix from a board concurrency token."""
        normalized = "".join(
            character
            for character in source_board_concurrency_token.lower()
            if character.isascii() and character.isalnum()
        )[:8]
        return normalized or "unknown000"

    @staticmethod
    def create_lane_queue_job_id(
        source_lane_id: str,
        source_board_concurrency_token: str,
    ) -> str:
        """Create a deterministic queue job ID from a lane ID and board token.

        The job ID encodes the source lane and a short suffix derived from
        the board concurrency token, making it reproducible for the same
        lane + board-state pair.
        """
        return (
            f"overnight-lane-{source_lane_id}"
            f"-{QueueMaterializer._queue_token_suffix(source_board_concurrency_token)}"
        )

    @staticmethod
    def find_queue_job(
        queue_payload: dict[str, Any],
        queue_job_id: str,
    ) -> dict[str, Any] | None:
        """Find a job in the queue payload by job ID.

        Returns the matching job dict, or ``None`` if not found.
        """
        for job in queue_payload.get("jobs", []):
            if isinstance(job, dict) and job.get("jobId") == queue_job_id:
                return job
        return None

    # ------------------------------------------------------------------
    # Queue status response
    # ------------------------------------------------------------------

    @staticmethod
    def overnight_queue_status_response() -> (
        DeveloperControlPlaneOvernightQueueStatusResponse
    ):
        """Build the overnight queue status API response.

        Loads the queue from the filesystem, validates its shape, computes
        the SHA256 hash, and delegates response building to the telemetry
        service.
        """
        queue_payload, exists = QueueMaterializer.load_overnight_queue_payload()
        queue_payload = validate_queue_payload_shape(queue_payload)
        response_dict = telemetry_service.build_overnight_queue_status_response(
            queue_payload,
            exists,
            QueueMaterializer.queue_sha256(queue_payload),
            _OVERNIGHT_QUEUE_PATH,
            _REPO_ROOT,
        )
        return DeveloperControlPlaneOvernightQueueStatusResponse(**response_dict)
