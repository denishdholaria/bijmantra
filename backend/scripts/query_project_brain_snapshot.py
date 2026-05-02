"""Query a file-backed project-brain bootstrap snapshot for developer inspection."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.ai.services.project_brain_query import render_project_brain_query_result
from app.modules.ai.services.project_brain_snapshot_query import ProjectBrainSnapshotQueryService


def _default_snapshot_path(repo_root: Path) -> Path:
    return repo_root / "backend" / "test_reports" / "project_brain_bootstrap_snapshot.json"


async def _run(snapshot_path: Path, query: str, as_json: bool, include_provenance: bool) -> None:
    if not snapshot_path.exists():
        raise SystemExit(f"Snapshot does not exist: {snapshot_path}")
    service = ProjectBrainSnapshotQueryService(snapshot_path)
    result = await service.query(query, include_provenance=include_provenance)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    print(render_project_brain_query_result(result))



def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Free-text query to run against the snapshot.")
    parser.add_argument(
        "--snapshot-path",
        default=str(_default_snapshot_path(repo_root)),
        help="Path to the JSON snapshot file to query.",
    )
    parser.add_argument("--json", action="store_true", help="Render the result as JSON.")
    parser.add_argument(
        "--no-provenance",
        action="store_true",
        help="Skip provenance trail lookup for matched nodes.",
    )
    args = parser.parse_args()
    asyncio.run(
        _run(
            Path(args.snapshot_path),
            args.query,
            as_json=args.json,
            include_provenance=not args.no_provenance,
        )
    )


if __name__ == "__main__":
    main()
