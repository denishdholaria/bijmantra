#!/usr/bin/env python3
# ruff: noqa: E402
"""Emit a governed Plant Vision JSONL manifest from a local dataset export.

This script expects a class-directory layout:

    dataset_root/
      Tomato___Late_blight/
        image1.jpg
      Tomato___healthy/
        image2.jpg

It does not download datasets or bypass provider terms. Download each dataset
from its source, then point this script at the local export.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.phenotyping.services.vision.dataset_governance_service import (
    DEFAULT_SPLITS,
    vision_dataset_governance_service,
)
from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    dataset_allows_project_use,
    get_public_dataset_catalog,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Catalog slug, for example plantvillage")
    parser.add_argument("--root", required=True, type=Path, help="Local dataset root")
    parser.add_argument("--crop", default="", help="Crop override used for canonical taxonomy")
    parser.add_argument(
        "--project-use",
        default=PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
        help="Allowed-use mode to validate, for example open_source_non_commercial",
    )
    parser.add_argument(
        "--terms-accepted-by",
        default=None,
        help="Required operator identifier for datasets that require manual access-term acceptance",
    )
    parser.add_argument("--seed", default=42, type=int, help="Deterministic split seed")
    parser.add_argument(
        "--preprocessing-version",
        default="vision-preprocess-v1",
        help="Preprocessing contract version",
    )
    parser.add_argument(
        "--split",
        default=None,
        choices=["train", "val", "test"],
        help="Deprecated compatibility option; deterministic split generation is preferred",
    )
    parser.add_argument(
        "--output", type=Path, help="Optional output JSONL path; defaults to stdout"
    )
    return parser.parse_args()


def iter_manifest_rows(
    dataset_slug: str,
    root: Path,
    *,
    crop: str,
    seed: int,
    preprocessing_version: str,
    project_use: str,
    terms_accepted_by: str | None,
    split_override: str | None,
) -> list[dict]:
    catalog = {entry.slug: entry for entry in get_public_dataset_catalog()}
    if dataset_slug not in catalog:
        valid = ", ".join(sorted(catalog))
        raise SystemExit(f"Unknown dataset slug '{dataset_slug}'. Valid slugs: {valid}")

    dataset = catalog[dataset_slug]
    if not dataset_allows_project_use(dataset, project_use):
        raise SystemExit(
            f"Dataset '{dataset_slug}' is not approved for project use '{project_use}'. "
            f"Allowed uses: {', '.join(dataset.allowed_uses) or 'none'}"
        )
    if dataset.requires_manual_access_acceptance and not terms_accepted_by:
        raise SystemExit(
            f"Dataset '{dataset_slug}' requires manual access terms acceptance. "
            "Pass --terms-accepted-by with the accepting operator identifier."
        )

    manifest = vision_dataset_governance_service.build_manifest(
        dataset_root=root,
        source=dataset,
        crop=crop,
        split_seed=seed,
        train_split=DEFAULT_SPLITS["train"],
        val_split=DEFAULT_SPLITS["val"],
        preprocessing_version=preprocessing_version,
        project_use=project_use,
    )
    if "error" in manifest:
        raise SystemExit(manifest["error"])
    rows = manifest["rows"]
    if split_override:
        rows = [{**row, "split": split_override} for row in rows]
    return rows


def main() -> int:
    args = parse_args()
    rows = iter_manifest_rows(
        args.dataset,
        args.root,
        crop=args.crop,
        seed=args.seed,
        preprocessing_version=args.preprocessing_version,
        project_use=args.project_use,
        terms_accepted_by=args.terms_accepted_by,
        split_override=args.split,
    )
    lines = [json.dumps(row, sort_keys=True) for row in rows]

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    else:
        sys.stdout.write("\n".join(lines))
        if lines:
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
