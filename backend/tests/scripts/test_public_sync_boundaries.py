from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_EXCLUDE_PATH = ROOT / ".public-exclude"

REQUIRED_PUBLIC_EXCLUDE_PATTERNS = {
    "ops-private/",
    ".openclaw/",
    ".nemoclaw/",
    "docker-compose.bijmantra.yml",
    "scripts/bjm-start.sh",
    "scripts/bijmantra_cron_bridge.py",
    "scripts/bijmantra_watchdog.py",
    "scripts/bijmantra_ctl.py",
    "scripts/sandbox_policy_manager.py",
}

EXPECTED_EXAMPLE_FILES = {
    ".openclaw.example/README.md",
    ".openclaw.example/agents.yaml",
    ".openclaw.example/bridge-config.yaml",
    ".openclaw.example/openclaw.json",
    ".nemoclaw.example/policies/bijmantra-sandbox.yaml",
}

FORBIDDEN_EXAMPLE_PATH_PARTS = {
    "agents/main",
    "auth-profiles.json",
    "cron-jobs",
    "cron-runs",
    "devices",
    "identity",
    "mission-evidence",
    "sessions",
    "watchdog-state.json",
    "watchdog.log",
    "workspace-state.json",
    "update-check.json",
    ".paused",
}


def _load_public_exclude_patterns() -> set[str]:
    lines = PUBLIC_EXCLUDE_PATH.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}


def test_public_sync_exclude_denies_runtime_and_operator_surfaces():
    patterns = _load_public_exclude_patterns()

    assert REQUIRED_PUBLIC_EXCLUDE_PATTERNS.issubset(patterns)


def test_example_runtime_dirs_only_keep_sanitized_bootstrap_files():
    example_paths = {
        str(path.relative_to(ROOT))
        for folder_name in (".openclaw.example", ".nemoclaw.example")
        for path in (ROOT / folder_name).rglob("*")
        if path.is_file()
    }

    assert EXPECTED_EXAMPLE_FILES.issubset(example_paths)

    for relative_path in example_paths:
        assert not any(part in relative_path for part in FORBIDDEN_EXAMPLE_PATH_PARTS), relative_path