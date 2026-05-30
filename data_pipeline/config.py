from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_DOMAINS = (
    "germplasm",
    "phenotyping",
    "genotyping",
    "trials",
    "observations",
    "gwas",
    "qtls",
)


@dataclass(slots=True)
class PipelineConfig:
    domains: list[str] = field(default_factory=lambda: list(DEFAULT_DOMAINS))
    dataset_size: str = "small"
    mode: str = "hybrid"
    organization_ids: list[int] = field(default_factory=lambda: [1, 2])
    output_dir: Path = Path("data_pipeline/output")
    raw_dir: Path = Path("data_pipeline/raw")
    transformed_dir: Path = Path("data_pipeline/transformed")
    synthetic_dir: Path = Path("data_pipeline/synthetic")
    seed: int = 1729
    crop_limit: int | None = None
    pipeline_version: str = "1.0.0"

    def resolved(self, repo_root: Path) -> PipelineConfig:
        clone = PipelineConfig(
            domains=list(self.domains),
            dataset_size=self.dataset_size,
            mode=self.mode,
            organization_ids=list(self.organization_ids),
            output_dir=_resolve_path(repo_root, self.output_dir),
            raw_dir=_resolve_path(repo_root, self.raw_dir),
            transformed_dir=_resolve_path(repo_root, self.transformed_dir),
            synthetic_dir=_resolve_path(repo_root, self.synthetic_dir),
            seed=self.seed,
            crop_limit=self.crop_limit,
            pipeline_version=self.pipeline_version,
        )
        return clone


def _resolve_path(repo_root: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo_root / value


def load_config(path: Path | None, repo_root: Path) -> PipelineConfig:
    if path is None:
        path = repo_root / "data_pipeline" / "config.yaml"
    if not path.exists():
        return PipelineConfig().resolved(repo_root)

    raw = _load_mapping(path)
    organization_id = raw.get("organization_id")
    organization_ids = raw.get("organization_ids")
    if organization_ids is None and organization_id is not None:
        organization_ids = [int(organization_id)]
    if organization_ids is None:
        organization_ids = [1, 2]

    return PipelineConfig(
        domains=list(raw.get("domains", DEFAULT_DOMAINS)),
        dataset_size=str(raw.get("dataset_size", "small")),
        mode=str(raw.get("mode", "hybrid")),
        organization_ids=[int(org_id) for org_id in organization_ids],
        output_dir=Path(str(raw.get("output_dir", "data_pipeline/output"))),
        raw_dir=Path(str(raw.get("raw_dir", "data_pipeline/raw"))),
        transformed_dir=Path(str(raw.get("transformed_dir", "data_pipeline/transformed"))),
        synthetic_dir=Path(str(raw.get("synthetic_dir", "data_pipeline/synthetic"))),
        seed=int(raw.get("seed", 1729)),
        crop_limit=_optional_int(raw.get("crop_limit")),
        pipeline_version=str(raw.get("pipeline_version", "1.0.0")),
    ).resolved(repo_root)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _simple_yaml_mapping(text)
    value = yaml.safe_load(text) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return value


def _simple_yaml_mapping(text: str) -> dict[str, Any]:
    """Tiny fallback parser for this config file when PyYAML is unavailable."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_key:
            result.setdefault(current_key, []).append(line[4:].strip())
            continue
        if ":" in line and not raw_line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                result[key] = value
            else:
                result[key] = []
    return result

