"""Bootstrap the project brain into the SurrealDB sidecar adapter."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.ai.services import ProjectBrainMemoryService
from app.modules.ai.services.project_brain_bootstrap import ProjectBrainBootstrapIngestionService
from app.modules.ai.services.project_brain_memory_surreal import (
    ProjectBrainSurrealConnectionConfig,
    SurrealProjectBrainMemoryRepository,
)
from app.modules.ai.services.project_brain_memory_surreal_schema import ProjectBrainSurrealSchemaManager


async def _run(
    config: ProjectBrainSurrealConnectionConfig,
    *,
    skip_health_check: bool,
    skip_schema_bootstrap: bool,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    schema_manager = ProjectBrainSurrealSchemaManager(config)
    repository = SurrealProjectBrainMemoryRepository(config)
    try:
        if not skip_health_check:
            healthy = await repository.check_health()
            if not healthy:
                raise SystemExit("SurrealDB health check did not report ready")
        if not skip_schema_bootstrap:
            schema_report = await schema_manager.ensure_schema()
            print(
                "Project-brain SurrealDB schema ensured "
                f"{config.namespace}/{config.database} at {config.base_url}"
            )
            print(schema_report.to_dict())
        service = ProjectBrainMemoryService(repository)
        bootstrap = ProjectBrainBootstrapIngestionService(service)
        report = await bootstrap.bootstrap_first_wave(repo_root)
        if report.missing_paths:
            missing = ", ".join(report.missing_paths)
            raise SystemExit(f"Bootstrap ingestion failed; missing first-wave paths: {missing}")
        print(
            "Project-brain SurrealDB bootstrap updated "
            f"{config.namespace}/{config.database} at {config.base_url}"
        )
        print(report.to_dict())
    finally:
        await schema_manager.aclose()
        await repository.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip the SurrealDB health probe before bootstrapping the first wave.",
    )
    parser.add_argument(
        "--skip-schema-bootstrap",
        action="store_true",
        help="Skip explicit SurrealDB schema and index bootstrap before loading the first wave.",
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
            skip_health_check=args.skip_health_check,
            skip_schema_bootstrap=args.skip_schema_bootstrap,
        )
    )


if __name__ == "__main__":
    main()
