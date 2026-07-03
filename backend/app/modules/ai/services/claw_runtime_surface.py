"""Runtime-surface helpers for external claw execution artifacts.

primary_domain = "ai_orchestration"
secondary_domains = ["operations", "developer_control_plane", "security"]
assumptions = [
    "The product repo should consume normalized runtime artifacts without requiring repo-local .openclaw ownership.",
    "The runtime artifacts directory may move outside the repo root during KRABI without changing API contracts.",
    "The overnight queue remains a product-repo contract even when runtime execution is externalized."
]
limitations = [
    "This helper only resolves file-backed runtime artifacts and does not yet support API-backed runtime providers.",
    "Historical evidence payloads may still contain legacy .openclaw source paths until writers are migrated.",
    "Execution-fabric scripts still own direct runtime paths until later KRABI slices decouple them."
]
uncertainty_handling = "Unknown or external runtime paths are normalized behind a stable runtime-artifacts display root rather than exposing local absolute paths."
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import settings
from app.modules.ai.services.claw_runtime_contract import (
    display_runtime_artifact_path as contract_display_runtime_artifact_path,
    resolve_claw_runtime_home,
    runtime_mission_evidence_dir,
    runtime_watchdog_state_path,
)


WATCHDOG_STATE_STALE_AFTER = timedelta(minutes=10)


def parse_runtime_timestamp(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def runtime_watchdog_state_freshness(
    last_check: str | None,
    *,
    now: datetime | None = None,
    stale_after: timedelta = WATCHDOG_STATE_STALE_AFTER,
) -> tuple[int | None, bool]:
    parsed = parse_runtime_timestamp(last_check)
    if parsed is None:
        return None, True

    reference_time = now or datetime.now(UTC)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=UTC)
    else:
        reference_time = reference_time.astimezone(UTC)

    age_seconds = max(0, int((reference_time - parsed).total_seconds()))
    return age_seconds, age_seconds > int(stale_after.total_seconds())


def resolve_runtime_artifacts_root(repo_root: Path) -> Path:
    return resolve_claw_runtime_home(repo_root, settings.DEVELOPER_CONTROL_PLANE_RUNTIME_ARTIFACTS_DIR)


def resolve_runtime_watchdog_state_path(repo_root: Path) -> Path:
    return runtime_watchdog_state_path(resolve_runtime_artifacts_root(repo_root))


def resolve_runtime_mission_evidence_dir(repo_root: Path) -> Path:
    return runtime_mission_evidence_dir(resolve_runtime_artifacts_root(repo_root))


def resolve_runtime_closeout_receipt_path(repo_root: Path, queue_job_id: str) -> Path:
    return resolve_runtime_mission_evidence_dir(repo_root) / queue_job_id / "closeout.json"


def display_runtime_artifact_path(repo_root: Path, path: Path) -> str:
    return contract_display_runtime_artifact_path(repo_root, resolve_runtime_artifacts_root(repo_root), path)