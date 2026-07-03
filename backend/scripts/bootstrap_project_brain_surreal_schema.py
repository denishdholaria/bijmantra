"""Ensure the SurrealDB schema and indexes for the project-brain sidecar."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.ai.services.project_brain_memory_surreal import ProjectBrainSurrealConnectionConfig
from app.modules.ai.services.project_brain_memory_surreal_schema import ProjectBrainSurrealSchemaManager


async def _run(config: ProjectBrainSurrealConnectionConfig) -> None:
    manager = ProjectBrainSurrealSchemaManager(config)
    try:
        report = await manager.ensure_schema()
        print(
            "Project-brain SurrealDB schema ensured "
            f"{config.namespace}/{config.database} at {config.base_url}"
        )
        print(report.to_dict())
    finally:
        await manager.aclose()


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
    args = parser.parse_args()
    asyncio.run(
        _run(
            ProjectBrainSurrealConnectionConfig(
                base_url=args.base_url,
                namespace=args.namespace,
                database=args.database,
                username=args.username,
                password=args.password,
            )
        )
    )


if __name__ == "__main__":
    main()
