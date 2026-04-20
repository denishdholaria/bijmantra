"""Query the persisted project-brain SurrealDB sidecar for developer inspection."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.ai.services import ProjectBrainMemoryService
from app.modules.ai.services.project_brain_query import (
    ProjectBrainQueryService,
    render_project_brain_query_result,
)
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    SurrealProjectBrainMemoryRepository,
)


async def _run(
    config: ProjectBrainSurrealConnectionConfig,
    query: str,
    *,
    as_json: bool,
    include_provenance: bool,
    skip_health_check: bool,
) -> None:
    repository = SurrealProjectBrainMemoryRepository(config)
    try:
        if not skip_health_check:
            healthy = await repository.check_health()
            if not healthy:
                raise SystemExit("SurrealDB health check did not report ready")
        memory_service = ProjectBrainMemoryService(repository)
        query_service = ProjectBrainQueryService(memory_service)
        result = await query_service.query(query, include_provenance=include_provenance)
        if as_json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return
        print(render_project_brain_query_result(result))
    finally:
        await repository.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Free-text query to run against the persistent sidecar.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8083",
        help="Dedicated Being Bijmantra SurrealDB HTTP base URL.",
    )
    parser.add_argument("--namespace", default="beingbijmantra", help="SurrealDB namespace.")
    parser.add_argument(
        "--database",
        default="beingbijmantra_surrealdb",
        help="SurrealDB database for the project-brain sidecar lane.",
    )
    parser.add_argument("--username", default="root", help="SurrealDB username.")
    parser.add_argument("--password", default="root", help="SurrealDB password.")
    parser.add_argument("--json", action="store_true", help="Render the result as JSON.")
    parser.add_argument(
        "--no-provenance",
        action="store_true",
        help="Skip provenance trail lookup for matched nodes.",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip the SurrealDB health probe before querying.",
    )
    args = parser.parse_args()
    asyncio.run(
        _run(
            ProjectBrainSurrealConnectionConfig(
                base_url=args.base_url,
                namespace=args.namespace,
                database=args.database,
                username=args.username,
                password=args.password,
            ),
            args.query,
            as_json=args.json,
            include_provenance=not args.no_provenance,
            skip_health_check=args.skip_health_check,
        )
    )


if __name__ == "__main__":
    main()
