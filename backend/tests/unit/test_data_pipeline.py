from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2].parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_schema_discovery_extracts_priority_models(tmp_path):
    from data_pipeline.discovery.schema_discovery import discover_schema

    schema = discover_schema(REPO_ROOT)

    assert schema["metrics"]["model_count"] >= 100
    assert "germplasm" in schema["tables"]
    assert "observations" in schema["tables"]
    assert "bio_gwas_runs" in schema["tables"]
    assert schema["tables"]["germplasm"]["columns"]["organization_id"]["required"] is True
    assert schema["domains"]["phenotyping"]["tables"]


def test_default_composition_produces_tenant_scoped_outputs(tmp_path):
    from data_pipeline.composer import compose_pipeline_output
    from data_pipeline.config import PipelineConfig
    from data_pipeline.validators.output_validator import validate_output_dir

    config = PipelineConfig(output_dir=tmp_path / "output", dataset_size="small")
    summary = compose_pipeline_output(config, REPO_ROOT)
    report = validate_output_dir(config.output_dir)

    assert summary["records"]["germplasm"] > 0
    assert summary["records"]["observations"] > 0
    assert report["validation_status"] == "passed"

    observations = json.loads((config.output_dir / "observations.json").read_text())
    assert observations["observation_units"]
    assert observations["observations"]
    assert {record["organization_id"] for record in observations["observations"]} == {1, 2}


def test_synthetic_traits_stay_in_domain_ranges():
    from data_pipeline.synthesizers.agronomic import synthesize_observation_value

    for trait_name in [
        "Grain Yield",
        "Plant Height",
        "Days to Flowering",
        "Blast Resistance",
        "Drought Tolerance",
    ]:
        values = [
            synthesize_observation_value(trait_name, crop_name="Rice", germplasm_index=i, seed=1729)
            for i in range(20)
        ]
        if trait_name in {"Blast Resistance", "Drought Tolerance"}:
            assert all(1 <= value <= 9 for value in values)
        else:
            assert all(value > 0 for value in values)


def test_raw_reader_parses_wrapped_public_sources(tmp_path):
    from data_pipeline.io import write_json
    from data_pipeline.transformers.raw_reader import RawDataReader

    raw_dir = tmp_path / "raw"
    write_json(
        raw_dir / "gbif_taxonomy.json",
        {"metadata": {}, "data": [{"_query_name": "Oryza sativa", "canonicalName": "Oryza sativa"}]},
    )
    write_json(
        raw_dir / "faostat_yield_baselines.json",
        {
            "metadata": {},
            "data": [
                {"Item": "Rice, paddy", "Value": 52000, "Unit": "hg/ha"},
                {"Item": "Rice, paddy", "Value": 54000, "Unit": "hg/ha"},
            ],
        },
    )
    write_json(
        raw_dir / "brapi_test_server_variables.json",
        {"metadata": {}, "data": {"result": {"data": [{"observationVariableName": "Grain Yield"}]}}},
    )

    reader = RawDataReader(raw_dir)

    assert "oryza sativa" in reader.gbif_taxonomy()
    assert reader.faostat_yield_baselines()["rice"]["unit"] == "kg/ha"
    assert reader.brapi_variables()[0]["observationVariableName"] == "Grain Yield"


def test_trait_registry_covers_catalog_categories():
    from data_pipeline.crop_catalog import load_crop_catalog
    from data_pipeline.transformers.trait_registry import get_traits_for_crop

    categories = {crop.category for crop in load_crop_catalog(REPO_ROOT)}

    for category in categories:
        assert len(get_traits_for_crop(category)) >= 5, category


def test_category_synthesizer_is_deterministic():
    from data_pipeline.synthesizers.agronomic import synthesize_observation_value

    first = synthesize_observation_value(
        "Fruit Yield",
        crop_name="Tomato",
        germplasm_index=2,
        valid_min=2,
        valid_max=120,
        seed=1729,
    )
    second = synthesize_observation_value(
        "Fruit Yield",
        crop_name="Tomato",
        germplasm_index=2,
        valid_min=2,
        valid_max=120,
        seed=1729,
    )

    assert first == second


def test_data_sources_have_three_sources_per_domain():
    from data_pipeline.sources import load_source_registry

    registry = load_source_registry(REPO_ROOT / "data_pipeline" / "data_sources.json")
    for domain, sources in registry.items():
        assert len(sources) >= 3, domain
        assert all(source["url"].startswith("http") for source in sources)
