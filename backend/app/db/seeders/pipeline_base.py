"""Shared helpers for JSON-backed data pipeline seeders."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.demo_dataset import is_production_environment


logger = logging.getLogger(__name__)


class PipelineSeederMixin:
    """Utilities shared by pipeline seeders.

    Seeders intentionally run only in non-production environments and only consume
    generated files from `data_pipeline/output`.
    """

    output_filename: str = ""
    is_demo_data = False

    def should_run(self, env: str = "dev") -> bool:
        return not is_production_environment(env)

    def pipeline_output_dir(self) -> Path:
        return find_pipeline_output_dir()

    def load_pipeline_output(self, default: Any) -> Any:
        path = self.pipeline_output_dir() / self.output_filename
        if not path.exists():
            logger.warning("Pipeline output file not found: %s", path)
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def resolve_record_org_id(self, requested_org_id: int) -> int | None:
        from app.db.seeders.demo_germplasm import get_or_create_demo_organization
        from app.models.core import Organization

        if requested_org_id == 2:
            return get_or_create_demo_organization(self.db).id
        org = self.db.query(Organization).filter(Organization.id == requested_org_id).first()
        if org is None:
            logger.warning("Pipeline target organization %s not found; skipping records", requested_org_id)
            return None
        return org.id


def pipeline_info(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_source": record.get("data_source"),
        "synthetic_method": record.get("synthetic_method"),
        "pipeline_version": record.get("pipeline_version"),
        "generated_at": record.get("generated_at"),
        "record_key": record.get("record_key"),
        "pipeline_record_key": record.get("record_key"),
    }


def find_pipeline_output_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "data_pipeline" / "output"


def find_pipeline_output(filename: str) -> Path:
    path = find_pipeline_output_dir() / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Pipeline output file not found: {path}. Run `uv run python -m data_pipeline run --no-fetch` first."
        )
    return path


def load_pipeline_output(filename: str) -> list[Any] | dict[str, Any]:
    return json.loads(find_pipeline_output(filename).read_text(encoding="utf-8"))


def is_pipeline_record(value: str, prefix: str = "pipeline_org") -> bool:
    return value.startswith(prefix)
