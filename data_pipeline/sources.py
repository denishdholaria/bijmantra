from __future__ import annotations

from pathlib import Path
from typing import Any

from data_pipeline.io import read_json


def load_source_registry(path: Path) -> dict[str, list[dict[str, Any]]]:
    registry = read_json(path)
    if not isinstance(registry, dict):
        raise ValueError(f"Data source registry must be a JSON object: {path}")
    return registry

