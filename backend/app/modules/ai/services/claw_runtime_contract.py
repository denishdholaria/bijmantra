"""Shared runtime-path contract for claw execution artifacts.

primary_domain = "ai_orchestration"
secondary_domains = ["operations", "developer_control_plane", "security"]
assumptions = [
    "The claw execution fabric may live outside the product repo while the product still consumes normalized runtime evidence.",
    "A single path contract should serve both backend runtime readers and operator-facing execution scripts.",
    "Legacy .openclaw references may still appear during transition and need normalization instead of abrupt rejection."
]
limitations = [
    "This contract only models file-backed runtime artifacts and not future API-backed runtime providers.",
    "It does not migrate existing files; callers still own any copy or extraction workflow.",
    "Legacy repo-local runtime folders may still exist during transition and are normalized only when encountered."
]
uncertainty_handling = "Runtime paths resolve from explicit configuration first, then fall back to the KRABI external-home default so callers avoid silent repo-local coupling."
"""

from __future__ import annotations

import os
from pathlib import Path

BIJMANTRA_CLAW_RUNTIME_HOME_ENV = "BIJMANTRA_CLAW_RUNTIME_HOME"
OPENCLAW_CONFIG_DIR_ENV = "OPENCLAW_CONFIG_DIR"
LEGACY_RUNTIME_DIRNAME = ".openclaw"  # DEPRECATED: Use runtime-artifacts/* display paths instead
LEGACY_NEMOCLAW_DIRNAME = ".nemoclaw"
RUNTIME_DISPLAY_ROOT = Path("runtime-artifacts")


def default_claw_runtime_home() -> Path:
    return Path.home() / ".bijmantra" / "runtime" / "claw"


def resolve_claw_runtime_home(repo_root: Path, configured_root: str | None = None) -> Path:
    selected_root = configured_root or os.getenv(BIJMANTRA_CLAW_RUNTIME_HOME_ENV) or os.getenv(OPENCLAW_CONFIG_DIR_ENV)
    runtime_root = Path(selected_root).expanduser() if selected_root else default_claw_runtime_home()
    if runtime_root.is_absolute():
        return runtime_root
    return (repo_root / runtime_root).resolve()


def legacy_claw_runtime_home(repo_root: Path) -> Path:
    return repo_root / LEGACY_RUNTIME_DIRNAME


def runtime_openclaw_config_path(runtime_root: Path) -> Path:
    return runtime_root / "openclaw.json"


def runtime_bridge_config_path(runtime_root: Path) -> Path:
    return runtime_root / "bridge-config.yaml"


def runtime_agents_config_path(runtime_root: Path) -> Path:
    return runtime_root / "agents.yaml"


def runtime_cron_jobs_dir(runtime_root: Path) -> Path:
    return runtime_root / "cron-jobs"


def runtime_cron_sync_state_path(runtime_root: Path) -> Path:
    return runtime_root / "cron-sync-state.json"


def runtime_auth_store_path(runtime_root: Path) -> Path:
    return runtime_root / "agents" / "main" / "agent" / "auth-profiles.json"


def runtime_watchdog_log_path(runtime_root: Path) -> Path:
    return runtime_root / "watchdog.log"


def runtime_watchdog_state_path(runtime_root: Path) -> Path:
    return runtime_root / "watchdog-state.json"


def runtime_mission_evidence_dir(runtime_root: Path) -> Path:
    return runtime_root / "mission-evidence"


def runtime_pause_file_path(runtime_root: Path) -> Path:
    return runtime_root / ".paused"


def display_runtime_artifact_path(repo_root: Path, runtime_root: Path, path: Path) -> str:
    for base in (runtime_root, legacy_claw_runtime_home(repo_root)):
        try:
            relative = path.relative_to(base)
        except ValueError:
            continue
        return str(RUNTIME_DISPLAY_ROOT / relative)

    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(RUNTIME_DISPLAY_ROOT / path.name)


def normalize_runtime_reference(repo_root: Path, runtime_root: Path, reference: str | Path | None) -> str | None:
    if reference is None:
        return None

    candidate = Path(reference).expanduser() if isinstance(reference, Path) else Path(reference.strip())
    if str(candidate) in {"", "."}:
        return None

    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve(strict=False)

    return display_runtime_artifact_path(repo_root, runtime_root, candidate)