from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data_pipeline import PIPELINE_VERSION
from data_pipeline.config import PipelineConfig
from data_pipeline.crop_catalog import TIER_1_CROPS, crop_intelligence, load_crop_catalog
from data_pipeline.discovery.schema_discovery import discover_schema
from data_pipeline.io import ensure_dirs, write_json
from data_pipeline.synthesizers.agronomic import (
    load_faostat_baselines,
    synthesize_observation_value,
    synthetic_method_for_trait,
)
from data_pipeline.transformers.raw_reader import RawDataReader
from data_pipeline.transformers.records import transform_crop_to_germplasm, transform_traits
from data_pipeline.transformers.trait_registry import get_traits_for_crop


def compose_pipeline_output(config: PipelineConfig, repo_root: Path) -> dict[str, Any]:
    config = config.resolved(repo_root)
    ensure_dirs(config.output_dir, config.transformed_dir, config.synthetic_dir)

    crop_limit = config.crop_limit or _crop_limit_for_size(config.dataset_size)
    crops = load_crop_catalog(repo_root, crop_limit=crop_limit)
    generated_at = datetime.now(UTC).isoformat()

    schema = discover_schema(repo_root)
    write_json(repo_root / "data_pipeline" / "schema_map.json", schema)

    raw_reader = RawDataReader(config.raw_dir)
    gbif_map = raw_reader.gbif_taxonomy()
    brapi_germplasm = raw_reader.brapi_germplasm()
    brapi_variables = raw_reader.brapi_variables()
    crop_ontology_traits = raw_reader.crop_ontology_traits()
    load_faostat_baselines(config.raw_dir)

    germplasm = []
    phenotyping = []
    trials_payload = {"programs": [], "locations": [], "seasons": [], "trials": [], "studies": []}
    observations_payload = {"observation_units": [], "observations": []}
    genotyping_payload = {
        "reference_sets": [],
        "references": [],
        "genome_maps": [],
        "linkage_groups": [],
        "variants": [],
        "call_sets": [],
        "calls": [],
    }
    gwas_payload = {"runs": [], "results": []}
    qtl_payload = {"qtls": [], "candidate_genes": []}
    seed_bank_payload = {"vaults": [], "accessions": [], "viability_tests": [], "regeneration_tasks": [], "exchanges": []}
    economics_payload = {"cost_benefit_analyses": [], "market_trends": []}
    field_payload = {"nursery_locations": [], "seedling_batches": [], "field_book_studies": [], "field_book_traits": [], "field_book_entries": [], "field_book_observations": []}
    social_payload = {"groups": [], "posts": [], "comments": [], "reactions": [], "reputation": []}

    for organization_id in config.organization_ids:
        org_crops = crops
        germplasm.extend(
            _with_metadata(record, config, generated_at)
            for crop in org_crops
            for record in transform_crop_to_germplasm(
                crop,
                organization_id,
                gbif_map=gbif_map,
                brapi_germplasm=brapi_germplasm,
            )
        )
        phenotyping.extend(
            _with_metadata(record, config, generated_at)
            for record in transform_traits(
                org_crops,
                organization_id,
                crop_ontology_traits=crop_ontology_traits,
                brapi_variables=brapi_variables,
            )
        )
        _extend_trials(trials_payload, org_crops, organization_id, config, generated_at)
        _extend_observations(
            observations_payload,
            org_crops,
            organization_id,
            config,
            generated_at,
        )
        _extend_genotyping(genotyping_payload, org_crops[: min(5, len(org_crops))], organization_id, config, generated_at)
        _extend_gwas(gwas_payload, org_crops[: min(5, len(org_crops))], organization_id, config, generated_at)
        _extend_qtls(qtl_payload, org_crops[: min(5, len(org_crops))], organization_id, config, generated_at)
        _extend_seed_bank(seed_bank_payload, org_crops[: min(8, len(org_crops))], organization_id, config, generated_at)
        _extend_economics(economics_payload, org_crops[: min(10, len(org_crops))], organization_id, config, generated_at)
        _extend_field(field_payload, org_crops[: min(4, len(org_crops))], organization_id, config, generated_at)
        _extend_social(social_payload, org_crops[: min(4, len(org_crops))], organization_id, config, generated_at)

    outputs = {
        "germplasm.json": germplasm,
        "phenotyping.json": {"observation_variables": phenotyping},
        "trials.json": trials_payload,
        "observations.json": observations_payload,
        "genotyping.json": genotyping_payload,
        "gwas.json": gwas_payload,
        "qtls.json": qtl_payload,
        "seed_bank.json": seed_bank_payload,
        "economics.json": economics_payload,
        "field_operations.json": field_payload,
        "social.json": social_payload,
    }
    for filename, payload in outputs.items():
        write_json(config.output_dir / filename, payload)

    # Phase artifacts: transformed keeps real/curated crop intelligence; synthetic keeps generated observations.
    write_json(
        config.transformed_dir / "crop_intelligence.json",
        [_with_metadata(crop_intelligence(crop), config, generated_at) for crop in crops],
    )
    write_json(config.synthetic_dir / "observations.json", observations_payload)

    return {
        "generated_at": generated_at,
        "pipeline_version": config.pipeline_version,
        "records": {
            "germplasm": len(germplasm),
            "observation_variables": len(phenotyping),
            "observation_units": len(observations_payload["observation_units"]),
            "observations": len(observations_payload["observations"]),
            "gwas_runs": len(gwas_payload["runs"]),
            "qtls": len(qtl_payload["qtls"]),
        },
    }


def _extend_trials(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    location_key = f"org{organization_id}:loc:research_station"
    location_name = (
        "Ludhiana Benchmark Research Station"
        if organization_id == 1
        else "Demo Pipeline Research Station"
    )
    geo_coordinates = (
        {"latitude": 30.9010, "longitude": 75.8573}
        if organization_id == 1
        else {"latitude": 28.61, "longitude": 77.21}
    )
    payload["locations"].append(
        _with_metadata(
            {
                "organization_id": organization_id,
                "record_key": location_key,
                "location_db_id": f"pipeline_org{organization_id}_research_station",
                "location_name": location_name,
                "location_type": "research_station",
                "country_name": "India",
                "country_code": "IND",
                "altitude": "215",
                "additional_info": {"geo_coordinates": geo_coordinates},
                "data_source": "synthetic",
                "synthetic_method": "deterministic_research_station_template",
            },
            config,
            generated_at,
        )
    )
    season_key = f"org{organization_id}:season:2025-kharif"
    payload["seasons"].append(
        _with_metadata(
            {
                "organization_id": organization_id,
                "record_key": season_key,
                "season_db_id": f"pipeline_org{organization_id}_2025_kharif",
                "season_name": "2025 Kharif",
                "year": 2025,
                "data_source": "synthetic",
                "synthetic_method": "season_template",
            },
            config,
            generated_at,
        )
    )
    program_groups = defaultdict(list)
    for crop in crops:
        program_groups[crop.category].append(crop)
    for program_index, (category, group_crops) in enumerate(program_groups.items(), start=1):
        program_key = f"org{organization_id}:program:{_slug(category)}"
        payload["programs"].append(
            _with_metadata(
                {
                    "organization_id": organization_id,
                    "record_key": program_key,
                    "program_db_id": f"pipeline_org{organization_id}_{_slug(category)}_program",
                    "program_name": f"{category} Improvement Program",
                    "abbreviation": f"PIP{program_index}",
                    "objective": f"Pipeline-derived {category.lower()} breeding and evaluation records",
                    "data_source": "hybrid",
                    "synthetic_method": "domain_program_template",
                },
                config,
                generated_at,
            )
        )
        for crop in group_crops:
            trial_key = f"org{organization_id}:{crop.crop_id}:trial:2025"
            study_key = f"org{organization_id}:{crop.crop_id}:study:2025"
            trial_name = (
                "Ludhiana Advanced Yield Trial 2025"
                if organization_id == 1 and crop.crop_id == "wheat"
                else f"{crop.common_name} Pipeline Yield Trial 2025"
            )
            payload["trials"].append(
                _with_metadata(
                    {
                        "organization_id": organization_id,
                        "record_key": trial_key,
                        "program_key": program_key,
                        "location_key": location_key,
                        "season_key": season_key,
                        "trial_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_trial_2025",
                        "trial_name": trial_name,
                        "trial_type": "Advanced Yield Trial",
                        "start_date": "2025-06-15",
                        "end_date": "2025-11-15",
                        "active": True,
                        "common_crop_name": crop.common_name,
                        "data_source": "hybrid",
                        "synthetic_method": "trial_template",
                    },
                    config,
                    generated_at,
                )
            )
            payload["studies"].append(
                _with_metadata(
                    {
                        "organization_id": organization_id,
                        "record_key": study_key,
                        "trial_key": trial_key,
                        "location_key": location_key,
                        "study_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_study_2025",
                        "study_name": f"{crop.common_name} Pipeline Study 2025",
                        "study_type": "Phenotyping",
                        "study_code": f"PIPE-{organization_id}-{crop.crop_id.upper()}-2025",
                        "start_date": "2025-06-15",
                        "end_date": "2025-11-15",
                        "active": True,
                        "common_crop_name": crop.common_name,
                        "observation_levels": ["plot"],
                        "data_source": "hybrid",
                        "synthetic_method": "study_template",
                    },
                    config,
                    generated_at,
                )
            )


def _extend_observations(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        for germplasm_index in range(1, 4):
            unit_key = f"org{organization_id}:{crop.crop_id}:unit:{germplasm_index}:2025"
            study_key = f"org{organization_id}:{crop.crop_id}:study:2025"
            germplasm_key = f"org{organization_id}:{crop.crop_id}:germplasm:{germplasm_index}"
            payload["observation_units"].append(
                _with_metadata(
                    {
                        "organization_id": organization_id,
                        "record_key": unit_key,
                        "study_key": study_key,
                        "germplasm_key": germplasm_key,
                        "observation_unit_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_unit_{germplasm_index}",
                        "observation_unit_name": f"{crop.common_name} Plot {germplasm_index:02d}",
                        "observation_level": "plot",
                        "position_coordinate_x": str(germplasm_index),
                        "position_coordinate_y": "A",
                        "entry_type": "test",
                        "geo_coordinates": {"geometry": {"type": "Point", "coordinates": [77.21, 28.61]}},
                        "data_source": "synthetic",
                        "synthetic_method": "plot_layout_template",
                    },
                    config,
                    generated_at,
                )
            )
            for trait in get_traits_for_crop(crop.category):
                trait_name = trait.trait_name
                value = synthesize_observation_value(
                    trait_name,
                    crop_name=crop.common_name,
                    germplasm_index=germplasm_index,
                    seed=config.seed,
                    valid_min=trait.valid_min,
                    valid_max=trait.valid_max,
                    nominal_values=trait.nominal_values,
                    data_type=trait.data_type,
                )
                payload["observations"].append(
                    _with_metadata(
                        {
                            "organization_id": organization_id,
                            "record_key": f"{unit_key}:obs:{_slug(trait_name)}",
                            "observation_unit_key": unit_key,
                            "observation_variable_key": f"org{organization_id}:{crop.crop_id}:trait:{trait_name}",
                            "study_key": study_key,
                            "germplasm_key": germplasm_key,
                            "observation_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_{germplasm_index}_{_slug(trait_name)}",
                            "collector": "BijMantra Data Pipeline",
                            "observation_time_stamp": "2025-09-15T10:00:00+00:00",
                            "value": str(value),
                            "geo_coordinates": {"geometry": {"type": "Point", "coordinates": [77.21, 28.61]}},
                            "data_source": "synthetic",
                            "synthetic_method": synthetic_method_for_trait(trait_name, crop.common_name),
                        },
                        config,
                        generated_at,
                    )
                )


def _extend_genotyping(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        ref_set_key = f"org{organization_id}:{crop.crop_id}:refset"
        payload["reference_sets"].append(_with_metadata({
            "organization_id": organization_id,
            "record_key": ref_set_key,
            "reference_set_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_refset",
            "reference_set_name": f"{crop.common_name} Pipeline Reference",
            "description": f"Source-registered reference placeholder for {crop.common_name}",
            "assembly_pui": f"pipeline:{crop.crop_id}:assembly",
            "species": {"term": crop.species},
            "data_source": "hybrid",
            "synthetic_method": "reference_metadata_template",
        }, config, generated_at))
        for chromosome in range(1, 4):
            reference_key = f"{ref_set_key}:chr{chromosome}"
            payload["references"].append(_with_metadata({
                "organization_id": organization_id,
                "record_key": reference_key,
                "reference_set_key": ref_set_key,
                "reference_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_chr{chromosome}",
                "reference_name": f"Chr{chromosome}",
                "length": 30_000_000 + chromosome * 1_000_000,
                "species": {"term": crop.species},
                "data_source": "synthetic",
                "synthetic_method": "chromosome_length_template",
            }, config, generated_at))
        map_key = f"org{organization_id}:{crop.crop_id}:map"
        payload["genome_maps"].append(_with_metadata({
            "organization_id": organization_id,
            "record_key": map_key,
            "map_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_map",
            "map_name": f"{crop.common_name} Pipeline SNP Map",
            "common_crop_name": crop.common_name,
            "type": "physical",
            "unit": "bp",
            "scientific_name": crop.scientific_name,
            "marker_count": 3,
            "data_source": "synthetic",
            "synthetic_method": "marker_map_template",
        }, config, generated_at))
        variant_keys: list[str] = []
        for chromosome in range(1, 4):
            payload["linkage_groups"].append(_with_metadata({
                "organization_id": organization_id,
                "map_key": map_key,
                "linkage_group_name": f"Chr{chromosome}",
                "max_position": float(30_000_000 + chromosome * 1_000_000),
                "marker_count": 1,
                "data_source": "synthetic",
                "synthetic_method": "linkage_group_template",
            }, config, generated_at))
            variant_key = f"{map_key}:variant:{chromosome}"
            variant_keys.append(variant_key)
            payload["variants"].append(_with_metadata({
                "organization_id": organization_id,
                "record_key": variant_key,
                "reference_key": f"{ref_set_key}:chr{chromosome}",
                "variant_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_snp_{chromosome}",
                "variant_name": f"{crop.crop_id.upper()}_SNP_{chromosome}",
                "variant_type": "SNP",
                "reference_bases": "A",
                "alternate_bases": ["G"],
                "start": chromosome * 1_000_000,
                "end": chromosome * 1_000_000 + 1,
                "data_source": "synthetic",
                "synthetic_method": "qtl_marker_template",
            }, config, generated_at))
        for germplasm_index, variety in enumerate(crop_intelligence(crop)["varieties"][:3], start=1):
            call_set_key = f"org{organization_id}:{crop.crop_id}:callset:{germplasm_index}"
            payload["call_sets"].append(_with_metadata({
                "organization_id": organization_id,
                "record_key": call_set_key,
                "call_set_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_callset_{germplasm_index}",
                "call_set_name": variety["name"],
                "sample_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_sample_{germplasm_index}",
                "data_source": "synthetic",
                "synthetic_method": "deterministic_training_population_callset",
            }, config, generated_at))
            for variant_index, variant_key in enumerate(variant_keys, start=1):
                dosage = (germplasm_index + variant_index + organization_id) % 3
                genotype_value = ("0/0", "0/1", "1/1")[dosage]
                payload["calls"].append(_with_metadata({
                    "organization_id": organization_id,
                    "record_key": f"{call_set_key}:call:{variant_index}",
                    "call_db_id": (
                        f"pipeline_org{organization_id}_{crop.crop_id}_"
                        f"call_{germplasm_index}_{variant_index}"
                    ),
                    "call_set_key": call_set_key,
                    "variant_key": variant_key,
                    "genotype_value": genotype_value,
                    "genotype": {"values": genotype_value.split("/")},
                    "data_source": "synthetic",
                    "synthetic_method": "deterministic_training_population_genotype",
                }, config, generated_at))


def _extend_gwas(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        run_key = f"org{organization_id}:{crop.crop_id}:gwas:grain_yield"
        payload["runs"].append(_with_metadata({
            "organization_id": organization_id,
            "record_key": run_key,
            "run_name": f"{crop.common_name} Pipeline Grain Yield GWAS 2025",
            "trait_name": "Grain Yield",
            "method": "MLM",
            "sample_size": 96,
            "marker_count": 4800,
            "significance_threshold": 0.000005,
            "significant_marker_count": 3,
            "manhattan_plot_data": [
                {"chromosome": str(i), "position": i * 1_000_000, "log_p": 6.2 + i / 3}
                for i in range(1, 4)
            ],
            "qq_plot_data": {"expected": [0.3, 0.6, 0.9], "observed": [0.35, 0.7, 1.05]},
            "data_source": "synthetic",
            "synthetic_method": "qtl_informed_gwas_template",
        }, config, generated_at))
        for index in range(1, 4):
            payload["results"].append(_with_metadata({
                "organization_id": organization_id,
                "run_key": run_key,
                "marker_name": f"{crop.crop_id.upper()}_SNP_{index}",
                "chromosome": str(index),
                "position": index * 1_000_000,
                "p_value": 10 ** -(6 + index / 4),
                "neg_log10_p": 6 + index / 4,
                "effect_size": round(0.25 + index * 0.08, 3),
                "standard_error": 0.08,
                "maf": 0.18 + index * 0.04,
                "is_significant": True,
                "data_source": "synthetic",
                "synthetic_method": "qtl_informed_marker_association",
            }, config, generated_at))


def _extend_qtls(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        for index, trait in enumerate(["Grain Yield", "Blast Resistance"], start=1):
            qtl_key = f"org{organization_id}:{crop.crop_id}:qtl:{_slug(trait)}"
            start = index * 9_000_000.0
            peak = start + 450_000.0
            end = start + 900_000.0
            payload["qtls"].append(_with_metadata({
                "organization_id": organization_id,
                "record_key": qtl_key,
                "qtl_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_qtl_{_slug(trait)}",
                "qtl_name": f"q{_slug(crop.common_name).upper()}{index}.1",
                "trait": trait,
                "population": f"{crop.common_name} Pipeline Mapping Population",
                "method": "CIM",
                "chromosome": str(index),
                "start_position": start,
                "end_position": end,
                "peak_position": peak,
                "lod": 5.8 + index,
                "lod_score": 5.8 + index,
                "pve": 11.0 + index * 3.5,
                "add_effect": 0.25 if trait == "Grain Yield" else -0.9,
                "marker_name": f"{crop.crop_id.upper()}_SNP_{index}",
                "confidence_interval_low": start + 100_000.0,
                "confidence_interval_high": end - 100_000.0,
                "candidate_genes": [{"gene_id": f"{crop.crop_id.upper()}_GENE_{index}"}],
                "data_source": "synthetic",
                "synthetic_method": "literature_shape_qtl_template",
            }, config, generated_at))
            payload["candidate_genes"].append(_with_metadata({
                "organization_id": organization_id,
                "qtl_key": qtl_key,
                "gene_id": f"{crop.crop_id.upper()}_GENE_{index}",
                "gene_name": f"{crop.common_name} candidate gene {index}",
                "chromosome": str(index),
                "start_position": int(peak - 25_000),
                "end_position": int(peak + 25_000),
                "source": "pipeline_candidate_gene_template",
                "description": f"Candidate gene near {trait} QTL peak for {crop.common_name}.",
                "go_terms": ["GO:0006952"] if trait == "Blast Resistance" else ["GO:0008152"],
                "data_source": "synthetic",
                "synthetic_method": "qtl_interval_candidate_template",
            }, config, generated_at))


def _extend_seed_bank(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    vault_key = f"org{organization_id}:seedbank:vault:active"
    payload["vaults"].append(_with_metadata({
        "organization_id": organization_id,
        "record_key": vault_key,
        "name": "Pipeline Active Vault",
        "type": "active",
        "temperature": 4.0,
        "humidity": 28.0,
        "capacity": 10000,
        "used": len(crops) * 300,
        "status": "optimal",
        "data_source": "synthetic",
        "synthetic_method": "seed_bank_vault_template",
    }, config, generated_at))
    for crop in crops:
        accession_key = f"org{organization_id}:{crop.crop_id}:seedbank:accession"
        payload["accessions"].append(_with_metadata({
            "organization_id": organization_id,
            "record_key": accession_key,
            "vault_key": vault_key,
            "accession_number": f"PIPE-SB-{organization_id}-{crop.crop_id.upper()}",
            "genus": crop.genus,
            "species": crop.species,
            "common_name": crop.common_name,
            "origin": "Pipeline source registry",
            "seed_count": 1000,
            "viability": 92.0,
            "status": "active",
            "data_source": "hybrid",
            "synthetic_method": "seed_bank_accession_template",
        }, config, generated_at))


def _extend_economics(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        intelligence = crop_intelligence(crop)
        payload["market_trends"].append(_with_metadata({
            "organization_id": organization_id,
            "crop_name": crop.common_name,
            "trait_name": "Grain Yield",
            "region": "India",
            "historical_data": [{"date": "2024-01-01", "value": intelligence["economics"]["market_price_usd_per_t"]}],
            "forecast_data": [{"date": "2026-01-01", "value": intelligence["economics"]["market_price_usd_per_t"] * 1.04, "confidence_interval": [0.9, 1.12]}],
            "forecast_method": "source_registry_plus_synthetic_smoothing",
            "accuracy_metric": 0.12,
            "data_source": "hybrid",
            "synthetic_method": "market_trend_projection",
        }, config, generated_at))


def _extend_field(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    location_key = f"org{organization_id}:nursery:main"
    payload["nursery_locations"].append(_with_metadata({
        "organization_id": organization_id,
        "record_key": location_key,
        "name": "Pipeline Nursery A",
        "location_type": "greenhouse",
        "capacity": 2500,
        "description": "Tenant-scoped pipeline nursery",
        "data_source": "synthetic",
        "synthetic_method": "nursery_template",
    }, config, generated_at))
    for index, crop in enumerate(crops, start=1):
        payload["seedling_batches"].append(_with_metadata({
            "organization_id": organization_id,
            "location_key": location_key,
            "germplasm_key": f"org{organization_id}:{crop.crop_id}:germplasm:1",
            "batch_code": f"PIPE-NB-{organization_id}-{index:03d}",
            "germplasm_name": crop.common_name,
            "sowing_date": "2025-06-01",
            "quantity_sown": 120,
            "quantity_germinated": 108,
            "quantity_healthy": 101,
            "status": "growing",
            "data_source": "synthetic",
            "synthetic_method": "nursery_batch_template",
        }, config, generated_at))


def _extend_social(payload: dict[str, list[dict[str, Any]]], crops, organization_id: int, config: PipelineConfig, generated_at: str) -> None:
    for crop in crops:
        group_key = f"org{organization_id}:{crop.crop_id}:group"
        payload["groups"].append(_with_metadata({
            "organization_id": organization_id,
            "record_key": group_key,
            "name": f"{crop.common_name} Pipeline Circle",
            "description": f"Tenant-safe synthetic knowledge group for {crop.common_name}.",
            "crop_type": crop.common_name,
            "is_private": False,
            "member_count": 0,
            "data_source": "synthetic",
            "synthetic_method": "social_group_template",
        }, config, generated_at))


def _with_metadata(record: dict[str, Any], config: PipelineConfig, generated_at: str) -> dict[str, Any]:
    enriched = dict(record)
    enriched.setdefault("data_source", config.mode if config.mode != "hybrid" else "hybrid")
    enriched.setdefault("synthetic_method", None)
    enriched["pipeline_version"] = config.pipeline_version or PIPELINE_VERSION
    enriched["generated_at"] = generated_at
    return enriched


def _crop_limit_for_size(dataset_size: str) -> int:
    return {
        "small": len(TIER_1_CROPS),
        "medium": 40,
        "large": 142,
    }.get(dataset_size, len(TIER_1_CROPS))


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_").replace("/", "_").replace("&", "and").replace("-", "_")
