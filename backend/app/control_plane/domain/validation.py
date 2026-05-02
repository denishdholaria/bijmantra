"""Pure validation functions for the Control Plane domain layer.

All functions in this module are infrastructure-free: no database, filesystem,
or HTTP imports.  Validation failures are signalled via :class:`DomainValidationError`
(or its subclass :class:`DuplicateJobIdError`).  The API layer is responsible for
translating these into the appropriate HTTP responses.

Extracted from ``backend/app/api/v2/developer_control_plane.py``.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants (queue-shape validation)
# ---------------------------------------------------------------------------

QUEUE_LANGUAGE = "en"
QUEUE_VOCABULARY_POLICY = "english-technical-only"


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class DomainValidationError(Exception):
    """Raised when a domain validation rule is violated.

    Attributes
    ----------
    status_code : int
        The HTTP-equivalent status code (e.g. 400, 409, 500).
    detail : str | dict[str, Any]
        A human-readable message or structured conflict detail.
    """

    def __init__(self, status_code: int, detail: str | dict[str, Any]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail if isinstance(detail, str) else str(detail))


class DuplicateJobIdError(DomainValidationError):
    """Raised when a queue entry has a duplicate job ID.

    Carries the ``job_id`` so the caller can build the appropriate conflict
    detail payload.
    """

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(
            status_code=409,
            detail=f"Queue entry conflict; jobId '{job_id}' already exists and create-only policy forbids overwrite",
        )


# ---------------------------------------------------------------------------
# ASCII text validation helpers
# ---------------------------------------------------------------------------


def require_ascii_text(value: Any, field_name: str) -> str:
    """Validate that *value* is a non-empty ASCII string.

    Raises :class:`DomainValidationError` (400) on failure.
    """
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(
            status_code=400,
            detail=f"{field_name} must be a non-empty string",
        )
    if not value.isascii():
        raise DomainValidationError(
            status_code=400,
            detail=f"{field_name} must use ASCII-only English technical vocabulary",
        )
    return value


def require_ascii_text_list(
    value: Any, field_name: str, *, min_items: int = 0
) -> list[str]:
    """Validate that *value* is a list of ASCII strings.

    Raises :class:`DomainValidationError` (400) on failure.
    """
    if not isinstance(value, list) or len(value) < min_items:
        minimum = f" with at least {min_items} item(s)" if min_items else ""
        raise DomainValidationError(
            status_code=400,
            detail=f"{field_name} must be a list{minimum}",
        )
    return [
        require_ascii_text(item, f"{field_name}[{index}]")
        for index, item in enumerate(value)
    ]


def optional_ascii_text(value: Any, field_name: str) -> str | None:
    """Validate an optional ASCII string (``None`` passes through)."""
    if value is None:
        return None
    return require_ascii_text(value, field_name)


def best_effort_ascii_text(value: Any) -> str | None:
    """Return a stripped ASCII string if possible, otherwise ``None``.

    Unlike :func:`require_ascii_text` this never raises.
    """
    if isinstance(value, str) and value.strip() and value.isascii():
        return value.strip()
    return None


# ---------------------------------------------------------------------------
# Queue payload validation
# ---------------------------------------------------------------------------


def validate_queue_payload_shape(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the top-level structure of an overnight queue payload.

    Raises :class:`DomainValidationError` (500) if the payload is malformed.
    """
    defaults = payload.get("defaults")
    jobs = payload.get("jobs")

    if payload.get("language") != QUEUE_LANGUAGE:
        raise DomainValidationError(
            status_code=500,
            detail="Overnight queue payload must declare language=en",
        )
    if payload.get("vocabularyPolicy") != QUEUE_VOCABULARY_POLICY:
        raise DomainValidationError(
            status_code=500,
            detail="Overnight queue payload must declare vocabularyPolicy=english-technical-only",
        )
    if not isinstance(defaults, dict):
        raise DomainValidationError(
            status_code=500,
            detail="Overnight queue payload defaults must be an object",
        )
    if not isinstance(jobs, list):
        raise DomainValidationError(
            status_code=500,
            detail="Overnight queue payload jobs must be a list",
        )

    return payload


def validate_queue_entry(
    queue_entry: dict[str, Any],
    existing_job_ids: set[str],
) -> dict[str, Any]:
    """Validate a single queue entry against the overnight-queue schema.

    Raises :class:`DomainValidationError` (400) for schema violations and
    :class:`DuplicateJobIdError` (409) when the job ID already exists.
    """
    required_keys = (
        "jobId",
        "title",
        "status",
        "priority",
        "primaryAgent",
        "supportAgents",
        "executionMode",
        "autonomousTrigger",
        "dependsOn",
        "goal",
        "lane",
        "successCriteria",
        "verification",
    )
    for key in required_keys:
        if key not in queue_entry:
            raise DomainValidationError(
                status_code=400,
                detail=f"queue_entry is missing required key: {key}",
            )

    job_id = require_ascii_text(queue_entry["jobId"], "queue_entry.jobId")
    if job_id in existing_job_ids:
        raise DuplicateJobIdError(job_id)

    if queue_entry["status"] != "queued":
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.status must be queued",
        )
    if queue_entry["priority"] != "p2":
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.priority must be p2",
        )
    if queue_entry["executionMode"] != "same-control-plane":
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.executionMode must be same-control-plane",
        )

    require_ascii_text(queue_entry["title"], "queue_entry.title")
    require_ascii_text(queue_entry["primaryAgent"], "queue_entry.primaryAgent")
    require_ascii_text(queue_entry["goal"], "queue_entry.goal")
    require_ascii_text_list(queue_entry["supportAgents"], "queue_entry.supportAgents")
    depends_on = require_ascii_text_list(queue_entry["dependsOn"], "queue_entry.dependsOn")
    success_criteria = require_ascii_text_list(
        queue_entry["successCriteria"],
        "queue_entry.successCriteria",
        min_items=1,
    )

    for dependency in depends_on:
        if dependency not in existing_job_ids:
            raise DomainValidationError(
                status_code=400,
                detail=f"queue_entry.dependsOn references unknown jobId: {dependency}",
            )

    autonomous_trigger = queue_entry["autonomousTrigger"]
    if not isinstance(autonomous_trigger, dict):
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.autonomousTrigger must be an object",
        )
    if autonomous_trigger.get("type") != "overnight-window":
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.autonomousTrigger.type must be overnight-window",
        )
    if autonomous_trigger.get("window") != "nightly":
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.autonomousTrigger.window must be nightly",
        )
    if autonomous_trigger.get("enabled") is not True:
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.autonomousTrigger.enabled must be true",
        )

    verification = queue_entry["verification"]
    if not isinstance(verification, dict):
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.verification must be an object",
        )
    verification_commands = require_ascii_text_list(
        verification.get("commands"),
        "queue_entry.verification.commands",
    )
    if verification.get("stateRefreshRequired") is not True:
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.verification.stateRefreshRequired must be true",
        )

    lane = queue_entry["lane"]
    if not isinstance(lane, dict):
        raise DomainValidationError(
            status_code=400,
            detail="queue_entry.lane must be an object",
        )
    lane_objective = require_ascii_text(lane.get("objective"), "queue_entry.lane.objective")
    lane_inputs = require_ascii_text_list(lane.get("inputs"), "queue_entry.lane.inputs")
    lane_outputs = require_ascii_text_list(lane.get("outputs"), "queue_entry.lane.outputs")
    lane_dependencies = require_ascii_text_list(
        lane.get("dependencies"),
        "queue_entry.lane.dependencies",
    )
    lane_completion_criteria = require_ascii_text_list(
        lane.get("completion_criteria"),
        "queue_entry.lane.completion_criteria",
        min_items=1,
    )

    provenance = queue_entry.get("provenance")
    validated_provenance = None
    if provenance is not None:
        if not isinstance(provenance, dict):
            raise DomainValidationError(
                status_code=400,
                detail="queue_entry.provenance must be an object",
            )

        required_provenance_keys = (
            "candidateVersion",
            "exportedAt",
            "boardId",
            "boardTitle",
            "sourceBoardConcurrencyToken",
            "sourceLaneId",
            "precedence",
        )
        for key in required_provenance_keys:
            if key not in provenance:
                raise DomainValidationError(
                    status_code=400,
                    detail=f"queue_entry.provenance is missing required key: {key}",
                )

        precedence = provenance["precedence"]
        if not isinstance(precedence, dict):
            raise DomainValidationError(
                status_code=400,
                detail="queue_entry.provenance.precedence must be an object",
            )
        if precedence.get("canonicalPlanningSource") != "active-board":
            raise DomainValidationError(
                status_code=400,
                detail=(
                    "queue_entry.provenance.precedence."
                    "canonicalPlanningSource must be active-board"
                ),
            )
        if precedence.get("derivedExecutionSurface") != "overnight-queue":
            raise DomainValidationError(
                status_code=400,
                detail=(
                    "queue_entry.provenance.precedence."
                    "derivedExecutionSurface must be overnight-queue"
                ),
            )
        if precedence.get("exportDisposition") != "manual-candidate-only":
            raise DomainValidationError(
                status_code=400,
                detail=(
                    "queue_entry.provenance.precedence."
                    "exportDisposition must be manual-candidate-only"
                ),
            )
        if precedence.get("conflictResolution") != "board-wins-no-silent-overwrite":
            raise DomainValidationError(
                status_code=400,
                detail=(
                    "queue_entry.provenance.precedence."
                    "conflictResolution must be board-wins-no-silent-overwrite"
                ),
            )
        if precedence.get("staleIfSourceBoardChanges") is not True:
            raise DomainValidationError(
                status_code=400,
                detail=(
                    "queue_entry.provenance.precedence."
                    "staleIfSourceBoardChanges must be true"
                ),
            )

        validated_provenance = {
            "candidateVersion": require_ascii_text(
                provenance["candidateVersion"],
                "queue_entry.provenance.candidateVersion",
            ),
            "exportedAt": require_ascii_text(
                provenance["exportedAt"],
                "queue_entry.provenance.exportedAt",
            ),
            "boardId": require_ascii_text(
                provenance["boardId"],
                "queue_entry.provenance.boardId",
            ),
            "boardTitle": require_ascii_text(
                provenance["boardTitle"],
                "queue_entry.provenance.boardTitle",
            ),
            "sourceBoardConcurrencyToken": require_ascii_text(
                provenance["sourceBoardConcurrencyToken"],
                "queue_entry.provenance.sourceBoardConcurrencyToken",
            ),
            "sourceLaneId": require_ascii_text(
                provenance["sourceLaneId"],
                "queue_entry.provenance.sourceLaneId",
            ),
            "precedence": {
                "canonicalPlanningSource": "active-board",
                "derivedExecutionSurface": "overnight-queue",
                "exportDisposition": "manual-candidate-only",
                "conflictResolution": "board-wins-no-silent-overwrite",
                "staleIfSourceBoardChanges": True,
            },
        }

    validated_entry = {
        "jobId": job_id,
        "title": queue_entry["title"],
        "status": "queued",
        "priority": "p2",
        "primaryAgent": queue_entry["primaryAgent"],
        "supportAgents": queue_entry["supportAgents"],
        "executionMode": "same-control-plane",
        "autonomousTrigger": {
            "type": "overnight-window",
            "window": "nightly",
            "enabled": True,
        },
        "dependsOn": depends_on,
        "goal": queue_entry["goal"],
        "lane": {
            "objective": lane_objective,
            "inputs": lane_inputs,
            "outputs": lane_outputs,
            "dependencies": lane_dependencies,
            "completion_criteria": lane_completion_criteria,
        },
        "successCriteria": success_criteria,
        "verification": {
            "commands": verification_commands,
            "stateRefreshRequired": True,
        },
    }

    if validated_provenance is not None:
        validated_entry["provenance"] = validated_provenance

    return validated_entry


# ---------------------------------------------------------------------------
# Closeout receipt contract builder (pure helper)
# ---------------------------------------------------------------------------


def build_closeout_receipt_contract(
    *,
    queue_job_id: str,
    artifact_paths: list[str],
    mission_id: str | None = None,
    producer_key: str | None = None,
    source_lane_id: str | None = None,
    source_board_concurrency_token: str | None = None,
    runtime_profile_id: str | None = None,
    runtime_policy_sha256: str | None = None,
    closeout_status: str | None = None,
    state_refresh_required: bool | None = None,
    receipt_recorded_at: str | None = None,
    verification_evidence_ref: str | None = None,
    queue_sha256_at_closeout: str | None = None,
) -> dict[str, Any]:
    """Build a closeout receipt contract dict from validated fields."""
    contract: dict[str, Any] = {
        "queue_job_id": queue_job_id,
        "artifact_paths": artifact_paths,
    }
    if mission_id is not None:
        contract["mission_id"] = mission_id
    if producer_key is not None:
        contract["producer_key"] = producer_key
    if source_lane_id is not None:
        contract["source_lane_id"] = source_lane_id
    if source_board_concurrency_token is not None:
        contract["source_board_concurrency_token"] = source_board_concurrency_token
    if runtime_profile_id is not None:
        contract["runtime_profile_id"] = runtime_profile_id
    if runtime_policy_sha256 is not None:
        contract["runtime_policy_sha256"] = runtime_policy_sha256
    if closeout_status is not None:
        contract["closeout_status"] = closeout_status
    if state_refresh_required is not None:
        contract["state_refresh_required"] = state_refresh_required
    if receipt_recorded_at is not None:
        contract["receipt_recorded_at"] = receipt_recorded_at
    if verification_evidence_ref is not None:
        contract["verification_evidence_ref"] = verification_evidence_ref
    if queue_sha256_at_closeout is not None:
        contract["queue_sha256_at_closeout"] = queue_sha256_at_closeout
    return contract


# ---------------------------------------------------------------------------
# Completion payload validation
# ---------------------------------------------------------------------------


def validate_completion_payload(
    payload: Any,
) -> dict[str, Any]:
    """Validate a lane completion payload.

    Expects an object with attributes ``source_lane_id``, ``queue_job_id``,
    ``closure_summary``, ``evidence``, and an optional ``closeout_receipt``
    (which itself has typed attributes).

    Returns a validated dict ready for downstream processing.

    Raises :class:`DomainValidationError` (400) on validation failure.
    """
    validated_closeout_receipt = None
    if payload.closeout_receipt is not None:
        validated_closeout_receipt = build_closeout_receipt_contract(
            queue_job_id=require_ascii_text(
                payload.closeout_receipt.queue_job_id,
                "completion.closeout_receipt.queue_job_id",
            ),
            artifact_paths=require_ascii_text_list(
                payload.closeout_receipt.artifact_paths,
                "completion.closeout_receipt.artifact_paths",
                min_items=0,
            ),
            mission_id=optional_ascii_text(
                payload.closeout_receipt.mission_id,
                "completion.closeout_receipt.mission_id",
            ),
            producer_key=optional_ascii_text(
                payload.closeout_receipt.producer_key,
                "completion.closeout_receipt.producer_key",
            ),
            source_lane_id=optional_ascii_text(
                payload.closeout_receipt.source_lane_id,
                "completion.closeout_receipt.source_lane_id",
            ),
            source_board_concurrency_token=optional_ascii_text(
                payload.closeout_receipt.source_board_concurrency_token,
                "completion.closeout_receipt.source_board_concurrency_token",
            ),
            runtime_profile_id=optional_ascii_text(
                payload.closeout_receipt.runtime_profile_id,
                "completion.closeout_receipt.runtime_profile_id",
            ),
            runtime_policy_sha256=optional_ascii_text(
                payload.closeout_receipt.runtime_policy_sha256,
                "completion.closeout_receipt.runtime_policy_sha256",
            ),
            closeout_status=optional_ascii_text(
                payload.closeout_receipt.closeout_status,
                "completion.closeout_receipt.closeout_status",
            ),
            state_refresh_required=payload.closeout_receipt.state_refresh_required,
            receipt_recorded_at=optional_ascii_text(
                payload.closeout_receipt.receipt_recorded_at,
                "completion.closeout_receipt.receipt_recorded_at",
            ),
            verification_evidence_ref=optional_ascii_text(
                payload.closeout_receipt.verification_evidence_ref,
                "completion.closeout_receipt.verification_evidence_ref",
            ),
            queue_sha256_at_closeout=optional_ascii_text(
                payload.closeout_receipt.queue_sha256_at_closeout,
                "completion.closeout_receipt.queue_sha256_at_closeout",
            ),
        )

    return {
        "source_lane_id": require_ascii_text(payload.source_lane_id, "completion.source_lane_id"),
        "queue_job_id": require_ascii_text(payload.queue_job_id, "completion.queue_job_id"),
        "closure_summary": require_ascii_text(
            payload.closure_summary,
            "completion.closure_summary",
        ),
        "evidence": require_ascii_text_list(payload.evidence, "completion.evidence", min_items=1),
        "closeout_receipt": validated_closeout_receipt,
    }
