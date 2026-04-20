"""Helpers for the tracked developer control-plane completion-assist artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_developer_control_plane_completion_assist_path(repo_root: Path) -> Path:
    return (
        repo_root
        / ".github"
        / "docs"
        / "architecture"
        / "tracking"
        / "developer-control-plane-completion-assist.json"
    )


def load_developer_control_plane_completion_assist(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(
            "Developer control-plane completion-assist payload must be a JSON object"
        )
    return payload