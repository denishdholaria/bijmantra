from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
ENV_VAR = "BIJMANTRA_CONFIDENTIAL_DOCS_ROOT"
DEFAULT_CONFIDENTIAL_DOCS_ROOT = WORKSPACE_ROOT / "confidential-docs"
LEGACY_PRIVATE_DOCS_ROOT = ROOT / "docs-private"


def resolve_confidential_docs_root() -> Path:
    configured_root = os.environ.get(ENV_VAR)
    candidates: list[Path] = []
    if configured_root:
        candidates.append(Path(configured_root).expanduser())
    candidates.append(DEFAULT_CONFIDENTIAL_DOCS_ROOT)
    if LEGACY_PRIVATE_DOCS_ROOT.exists():
        candidates.append(LEGACY_PRIVATE_DOCS_ROOT)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0].resolve()


def display_path(path: Path, repo_root: Path = ROOT) -> str:
    resolved_path = path.resolve()
    repo_root = repo_root.resolve()
    for base in (repo_root, repo_root.parent):
        try:
            return str(resolved_path.relative_to(base))
        except ValueError:
            continue
    return str(resolved_path)