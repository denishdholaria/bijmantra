from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st


REPO_ROOT = Path(__file__).resolve().parents[2].parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_pipeline_output_integrity_properties(tmp_path):
    from data_pipeline.composer import compose_pipeline_output
    from data_pipeline.config import PipelineConfig
    from data_pipeline.validators.output_validator import validate_output_dir

    config = PipelineConfig(
        output_dir=tmp_path / "output",
        transformed_dir=tmp_path / "transformed",
        synthetic_dir=tmp_path / "synthetic",
        raw_dir=REPO_ROOT / "data_pipeline" / "raw",
        dataset_size="small",
        organization_ids=[1, 2],
    )
    compose_pipeline_output(config, REPO_ROOT)
    report = validate_output_dir(config.output_dir)
    outputs = _read_outputs(config.output_dir)
    records = list(_iter_output_records(outputs))

    assert report["validation_status"] == "passed"
    assert report["errors"] == []
    assert records

    for _table, record in records:
        assert isinstance(record.get("organization_id"), int)
        assert record["organization_id"] in {1, 2}
        assert record.get("data_source") in {"real", "synthetic", "hybrid"}
        assert record.get("pipeline_version")
        assert record.get("generated_at")
        if record.get("data_source") == "synthetic":
            assert record.get("synthetic_method")

    _assert_references_resolve(outputs)


def test_large_pipeline_trait_coverage_and_alignment(tmp_path):
    from data_pipeline.composer import compose_pipeline_output
    from data_pipeline.config import PipelineConfig
    from data_pipeline.crop_catalog import load_crop_catalog
    from data_pipeline.transformers.trait_registry import get_traits_for_crop
    from data_pipeline.validators.output_validator import validate_output_dir

    config = PipelineConfig(
        output_dir=tmp_path / "large-output",
        transformed_dir=tmp_path / "large-transformed",
        synthetic_dir=tmp_path / "large-synthetic",
        raw_dir=REPO_ROOT / "data_pipeline" / "raw",
        dataset_size="large",
        organization_ids=[1],
    )
    summary = compose_pipeline_output(config, REPO_ROOT)
    report = validate_output_dir(config.output_dir)
    phenotyping = json.loads((config.output_dir / "phenotyping.json").read_text())
    variables = phenotyping["observation_variables"]
    crop_by_name = {crop.common_name: crop for crop in load_crop_catalog(REPO_ROOT)}
    traits_by_crop: dict[str, set[str]] = {}

    for variable in variables:
        crop = crop_by_name[variable["common_crop_name"]]
        allowed_traits = {trait.trait_name for trait in get_traits_for_crop(crop.category)}
        assert variable["trait_name"] in allowed_traits
        traits_by_crop.setdefault(crop.common_name, set()).add(variable["trait_name"])

    assert summary["records"]["observation_variables"] >= 710
    assert report["validation_status"] == "passed"
    assert report["errors"] == []
    assert all(len(traits) >= 5 for traits in traits_by_crop.values())


_DETERMINISM_CASES = [
    ("Rice", "Grain Yield", 500, 12000, "Numerical", ()),
    ("Tomato", "Fruit Yield", 2, 120, "Numerical", ()),
    ("Potato", "Fresh Root Yield", 5, 90, "Numerical", ()),
    ("Sunflower", "Oil Content", 15, 60, "Numerical", ()),
    ("Cotton", "Fiber Length", 5, 3500, "Numerical", ()),
    ("Rice", "Blast Resistance", 1, 9, "Ordinal", ()),
    ("Potato", "Skin Color", None, None, "Nominal", ("white", "yellow", "red")),
]


@settings(max_examples=50)
@given(
    case=st.sampled_from(_DETERMINISM_CASES),
    germplasm_index=st.integers(min_value=1, max_value=8),
    study_index=st.integers(min_value=0, max_value=4),
)
def test_synthesizer_determinism_property(case, germplasm_index, study_index):
    from data_pipeline.synthesizers.agronomic import synthesize_observation_value

    crop_name, trait_name, valid_min, valid_max, data_type, nominal_values = case
    first = synthesize_observation_value(
        trait_name,
        crop_name=crop_name,
        germplasm_index=germplasm_index,
        study_index=study_index,
        seed=1729,
        valid_min=valid_min,
        valid_max=valid_max,
        data_type=data_type,
        nominal_values=nominal_values,
    )
    second = synthesize_observation_value(
        trait_name,
        crop_name=crop_name,
        germplasm_index=germplasm_index,
        study_index=study_index,
        seed=1729,
        valid_min=valid_min,
        valid_max=valid_max,
        data_type=data_type,
        nominal_values=nominal_values,
    )

    assert first == second


def test_fetch_resilience_property(monkeypatch, tmp_path):
    from data_pipeline.composer import compose_pipeline_output
    from data_pipeline.config import PipelineConfig
    from data_pipeline.fetchers.base import BaseFetcher
    from data_pipeline.run import _fetch
    from data_pipeline.validators.output_validator import validate_output_dir

    async def fail_get_json(self, url, params=None):  # noqa: ARG001
        raise RuntimeError("offline test")

    monkeypatch.setattr(BaseFetcher, "_get_json", fail_get_json)
    config = PipelineConfig(
        raw_dir=tmp_path / "raw",
        output_dir=tmp_path / "output",
        transformed_dir=tmp_path / "transformed",
        synthetic_dir=tmp_path / "synthetic",
        dataset_size="small",
        organization_ids=[1],
    )

    fetch_exit = asyncio.run(
        _fetch(
            config,
            ["gbif_taxonomy", "brapi_test_server", "brapi_germplasm", "faostat"],
            force_fetch=True,
            repo_root=REPO_ROOT,
        )
    )
    compose_pipeline_output(config, REPO_ROOT)
    report = validate_output_dir(config.output_dir)

    assert fetch_exit == 1
    assert report["validation_status"] == "passed"
    assert report["errors"] == []
    assert len(report["fetch_errors"]) >= 4


def _read_outputs(output_dir: Path) -> dict[str, Any]:
    return {
        path.stem: json.loads(path.read_text())
        for path in output_dir.glob("*.json")
    }


def _iter_output_records(outputs: dict[str, Any]):
    for table_name, payload in outputs.items():
        if isinstance(payload, list):
            for record in payload:
                yield table_name, record
        elif isinstance(payload, dict):
            for nested_name, records in payload.items():
                if isinstance(records, list):
                    for record in records:
                        yield nested_name, record


def _assert_references_resolve(outputs: dict[str, Any]) -> None:
    germplasm_keys = {record["record_key"] for record in outputs["germplasm"]}
    studies = outputs["trials"]["studies"]
    study_keys = {record["record_key"] for record in studies}
    variable_keys = {
        record["record_key"]
        for record in outputs["phenotyping"]["observation_variables"]
    }
    unit_keys = {
        record["record_key"]
        for record in outputs["observations"]["observation_units"]
    }
    run_keys = {record["record_key"] for record in outputs["gwas"]["runs"]}
    qtl_keys = {record["record_key"] for record in outputs["qtls"]["qtls"]}

    for unit in outputs["observations"]["observation_units"]:
        assert unit["study_key"] in study_keys
        assert unit["germplasm_key"] in germplasm_keys
    for observation in outputs["observations"]["observations"]:
        assert observation["observation_unit_key"] in unit_keys
        assert observation["observation_variable_key"] in variable_keys
        assert observation["study_key"] in study_keys
        assert observation["germplasm_key"] in germplasm_keys
    for result in outputs["gwas"]["results"]:
        assert result["run_key"] in run_keys
    for candidate in outputs["qtls"]["candidate_genes"]:
        assert candidate["qtl_key"] in qtl_keys
