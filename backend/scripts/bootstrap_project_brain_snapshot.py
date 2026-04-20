"""Generate a local file-backed bootstrap snapshot for the project brain."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.ai.services import FileBackedProjectBrainMemoryRepository, ProjectBrainMemoryService
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService


def _default_snapshot_path(repo_root: Path) -> Path:
    return repo_root / "backend" / "test_reports" / "project_brain_bootstrap_snapshot.json"


async def _run(snapshot_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repository = FileBackedProjectBrainMemoryRepository(snapshot_path)
    service = ProjectBrainMemoryService(repository)
    bootstrap = ProjectBrainBootstrapIngestionService(service)
    report = await bootstrap.bootstrap_first_wave(repo_root)
    if report.missing_paths:
        missing = ", ".join(report.missing_paths)
        raise SystemExit(f"Bootstrap ingestion failed; missing first-wave paths: {missing}")
    print(f"Project-brain snapshot updated: {snapshot_path}")
    print(report.to_dict())


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-path",
        default=str(_default_snapshot_path(repo_root)),
        help="Path to the JSON snapshot file to create or refresh.",
    )
    args = parser.parse_args()
    asyncio.run(_run(Path(args.snapshot_path)))


if __name__ == "__main__":
    main()
