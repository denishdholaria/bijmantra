"""Developer control-plane board validation and canonicalization helpers."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


DEVELOPER_MASTER_BOARD_SCHEMA_VERSION = "1.2.0"
DEVELOPER_MASTER_BOARD_SUPPORTED_IMPORT_VERSIONS = {"1.0.0", "1.1.0", "1.2.0"}
DEVELOPER_MASTER_BOARD_ID = "bijmantra-app-development-master-board"

DeveloperBoardStatus = Literal["active", "planned", "blocked", "watch", "completed"]


class DeveloperBoardSubplan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    objective: str
    status: DeveloperBoardStatus
    outputs: list[str]


class DeveloperBoardLaneCloseoutReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    queue_job_id: str
    artifact_paths: list[str]
    mission_id: str | None = None
    producer_key: str | None = None
    source_lane_id: str | None = None
    source_board_concurrency_token: str | None = None
    runtime_profile_id: str | None = None
    runtime_policy_sha256: str | None = None
    closeout_status: str | None = None
    state_refresh_required: bool | None = None
    receipt_recorded_at: str | None = None
    verification_evidence_ref: str | None = None
    queue_sha256_at_closeout: str | None = None


class DeveloperBoardLaneClosure(BaseModel):
    model_config = ConfigDict(extra="ignore")

    queue_job_id: str
    queue_sha256: str
    source_board_concurrency_token: str
    closure_summary: str
    evidence: list[str]
    completed_at: str
    closeout_receipt: DeveloperBoardLaneCloseoutReceipt | None = None


class DeveloperBoardLaneValidationBasis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    owner: str
    summary: str
    evidence: list[str]
    last_reviewed_at: str


class DeveloperBoardLaneReviewGate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reviewed_by: str
    summary: str
    evidence: list[str]
    reviewed_at: str


class DeveloperBoardLaneReviewState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    spec_review: DeveloperBoardLaneReviewGate | None = None
    risk_review: DeveloperBoardLaneReviewGate | None = None
    verification_evidence: DeveloperBoardLaneReviewGate | None = None


class DeveloperBoardLane(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    objective: str
    status: DeveloperBoardStatus
    owners: list[str]
    inputs: list[str]
    outputs: list[str]
    dependencies: list[str]
    completion_criteria: list[str]
    validation_basis: DeveloperBoardLaneValidationBasis | None = None
    review_state: DeveloperBoardLaneReviewState | None = None
    closure: DeveloperBoardLaneClosure | None = None
    subplans: list[DeveloperBoardSubplan]


class DeveloperBoardAgentRole(BaseModel):
    model_config = ConfigDict(extra="ignore")

    agent: str
    role: str
    reads: list[str]
    writes: list[str]
    escalation: list[str]


class DeveloperBoardOrchestrationContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    canonical_inputs: list[str]
    canonical_outputs: list[str]
    execution_loop: list[str]
    coordination_rules: list[str]


class DeveloperBoardControlPlane(BaseModel):
    model_config = ConfigDict(extra="ignore")

    primary_orchestrator: str
    evidence_sources: list[str]
    operating_cadence: list[str]


class DeveloperBoardAutonomyContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool
    allowed_lanes: list[str]
    allowed_tools: list[str]
    verification_required: bool
    stop_conditions: list[str]

    @field_validator("stop_conditions")
    @classmethod
    def validate_stop_conditions(cls, value: list[str]) -> list[str]:
        required_stops = {"human-gated", "review-required"}
        for r in required_stops:
            if r not in value:
                raise ValueError(f"stop condition '{r}' is required for safe autonomy")
        return value


class DeveloperMasterBoard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: str
    board_id: str
    title: str
    visibility: Literal["internal-superuser"]
    intent: str
    continuous_operation_goal: str
    orchestration_contract: DeveloperBoardOrchestrationContract
    lanes: list[DeveloperBoardLane]
    agent_roles: list[DeveloperBoardAgentRole]
    control_plane: DeveloperBoardControlPlane
    autonomy_contract: DeveloperBoardAutonomyContract | None = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value not in DEVELOPER_MASTER_BOARD_SUPPORTED_IMPORT_VERSIONS:
            raise ValueError(
                f"unsupported schema version {json.dumps(value)}; supported import versions: {', '.join(sorted(DEVELOPER_MASTER_BOARD_SUPPORTED_IMPORT_VERSIONS))}; current export version: {DEVELOPER_MASTER_BOARD_SCHEMA_VERSION}"
            )
        return value

    @field_validator("board_id")
    @classmethod
    def validate_board_id(cls, value: str) -> str:
        if value != DEVELOPER_MASTER_BOARD_ID:
            raise ValueError(
                f"unsupported board_id {json.dumps(value)}; expected {DEVELOPER_MASTER_BOARD_ID}"
            )
        return value


def canonicalize_developer_master_board_json(raw_board_json: str) -> tuple[str, DeveloperMasterBoard]:
    try:
        parsed = json.loads(raw_board_json)
    except json.JSONDecodeError as exc:
        raise ValueError("malformed JSON") from exc

    try:
        board = DeveloperMasterBoard.model_validate(parsed)
    except ValidationError as exc:
        first_error = exc.errors()[0]
        location = ".".join(str(part) for part in first_error.get("loc", []))
        message = first_error.get("msg", "invalid board structure")
        if location:
            raise ValueError(f"{location}: {message}") from exc
        raise ValueError(message) from exc

    canonical_json = f"{json.dumps(board.model_dump(mode='python', exclude_none=True), indent=2)}\n"
    return canonical_json, board


def build_developer_master_board_summary(board: DeveloperMasterBoard) -> dict[str, Any]:
    subplan_count = sum(len(lane.subplans) for lane in board.lanes)
    active_lane_count = sum(1 for lane in board.lanes if lane.status == "active")

    return {
        "title": board.title,
        "lane_count": len(board.lanes),
        "subplan_count": subplan_count,
        "agent_role_count": len(board.agent_roles),
        "active_lane_count": active_lane_count,
        "visibility": board.visibility,
        "primary_orchestrator": board.control_plane.primary_orchestrator,
        "autonomy_enabled": board.autonomy_contract.enabled if board.autonomy_contract else False,
    }