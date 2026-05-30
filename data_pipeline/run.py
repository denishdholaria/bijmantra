from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from data_pipeline.composer import compose_pipeline_output
from data_pipeline.config import load_config
from data_pipeline.discovery.schema_discovery import discover_schema
from data_pipeline.fetchers.public_sources import FETCHER_REGISTRY
from data_pipeline.io import ensure_dirs, repo_root_from, write_json
from data_pipeline.validators.output_validator import validate_output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BijMantra data acquisition pipeline")
    parser.add_argument("command", choices=["discover", "fetch", "transform", "synthesize", "compose", "validate", "seed", "run"])
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--force-fetch", action="store_true", help="Bypass raw-data cache during fetch")
    parser.add_argument("--no-fetch", action="store_true", help="Skip fetch phase when running the full pipeline")
    args = parser.parse_args(argv)

    repo_root = repo_root_from(Path.cwd())
    config = load_config(args.config, repo_root)

    if args.command == "discover":
        write_json(repo_root / "data_pipeline" / "schema_map.json", discover_schema(repo_root))
        return 0
    if args.command == "fetch":
        return asyncio.run(_fetch(config, args.source, force_fetch=args.force_fetch, repo_root=repo_root))
    if args.command in {"transform", "synthesize", "compose"}:
        compose_pipeline_output(config, repo_root)
        return 0
    if args.command == "validate":
        report = validate_output_dir(config.output_dir)
        return 0 if report["validation_status"] == "passed" else 1
    if args.command == "seed":
        return _seed(repo_root)
    if args.command == "run":
        write_json(repo_root / "data_pipeline" / "schema_map.json", discover_schema(repo_root))
        if not args.no_fetch:
            asyncio.run(_fetch(config, args.source, force_fetch=args.force_fetch, repo_root=repo_root))
        compose_pipeline_output(config, repo_root)
        report = validate_output_dir(config.output_dir)
        return 0 if report["validation_status"] == "passed" else 1
    return 1


async def _fetch(
    config,
    source_names: list[str],
    *,
    force_fetch: bool = False,
    repo_root: Path | None = None,
) -> int:
    ensure_dirs(config.raw_dir)
    selected = source_names or [
        "gbif_taxonomy",
        "crop_ontology",
        "brapi_test_server",
        "brapi_germplasm",
        "faostat",
    ]
    failures = 0
    for source_name in selected:
        fetcher_class = FETCHER_REGISTRY.get(source_name)
        if fetcher_class is None:
            print(f"Unknown source: {source_name}")
            failures += 1
            continue
        try:
            result = await fetcher_class(config.raw_dir).fetch(
                force_fetch=force_fetch,
                repo_root=repo_root,
            )
            if result.ok:
                print(f"{source_name}: fetched {result.record_count} record(s) -> {result.raw_path}")
            else:
                failures += 1
                print(f"{source_name}: failed: {result.error}")
        except Exception as exc:
            failures += 1
            _write_fetch_error(config.raw_dir, source_name, exc)
            print(f"{source_name}: failed: {exc}")
    return 1 if failures else 0


def _write_fetch_error(raw_dir: Path, source_name: str, exc: Exception) -> None:
    write_json(
        raw_dir / f"{source_name}_error.json",
        {"source": source_name, "ok": False, "error": str(exc)},
    )


def _seed(repo_root: Path) -> int:
    print(
        "Seeder integration lives in backend/app/db/seeders. "
        "Run from backend with: PYTHONPATH=.. uv run python -m app.db.seed "
        "--only=pipeline_trials --only=pipeline_germplasm --only=pipeline_phenotyping "
        "--only=pipeline_observations --only=pipeline_genotyping --only=pipeline_gwas "
        "--only=pipeline_qtls --scope=system"
    )
    return 0
