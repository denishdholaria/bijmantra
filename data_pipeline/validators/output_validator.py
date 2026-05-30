from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from data_pipeline.io import read_json, write_json
from data_pipeline.transformers.raw_reader import RawDataReader


def validate_output_dir(output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    stats = {
        "total_records": 0,
        "real_records": 0,
        "synthetic_records": 0,
        "hybrid_records": 0,
    }

    files = {
        "germplasm": read_json(output_dir / "germplasm.json", default=[]),
        "phenotyping": read_json(output_dir / "phenotyping.json", default={"observation_variables": []}),
        "trials": read_json(output_dir / "trials.json", default={}),
        "observations": read_json(output_dir / "observations.json", default={}),
        "gwas": read_json(output_dir / "gwas.json", default={}),
        "qtls": read_json(output_dir / "qtls.json", default={}),
    }

    for table_name, records in _iter_records(files):
        for record in records:
            stats["total_records"] += 1
            source = record.get("data_source", "synthetic")
            if source in {"real", "synthetic", "hybrid"}:
                stats[f"{source}_records"] += 1
            if "organization_id" not in record:
                errors.append(_issue(table_name, "missing organization_id", record))
            if source == "synthetic" and not record.get("synthetic_method"):
                errors.append(_issue(table_name, "synthetic record missing synthetic_method", record))

    _validate_references(files, errors)
    _validate_business_rules(files, errors, warnings)
    _validate_trait_coverage(files, errors)
    _validate_real_data_ratio(stats, warnings)
    fetch_errors = RawDataReader(output_dir.parent / "raw").fetch_errors()

    stats["validation_time_ms"] = int((time.perf_counter() - started) * 1000)
    report = {
        "validation_status": "failed" if errors else "passed",
        "errors": errors,
        "warnings": warnings,
        "fetch_errors": fetch_errors,
        "stats": stats,
    }
    write_json(output_dir.parent / "validation_report.json", report)
    return report


def _iter_records(files: dict[str, Any]):
    yield "germplasm", files["germplasm"]
    yield "observation_variables", files["phenotyping"].get("observation_variables", [])
    for table_name in ("programs", "locations", "seasons", "trials", "studies"):
        yield table_name, files["trials"].get(table_name, [])
    for table_name in ("observation_units", "observations"):
        yield table_name, files["observations"].get(table_name, [])
    for table_name in ("runs", "results"):
        yield f"gwas_{table_name}", files["gwas"].get(table_name, [])
    for table_name in ("qtls", "candidate_genes"):
        yield table_name, files["qtls"].get(table_name, [])


def _validate_references(files: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    germplasm_keys = {record["record_key"] for record in files["germplasm"]}
    study_keys = {record["record_key"] for record in files["trials"].get("studies", [])}
    unit_keys = {record["record_key"] for record in files["observations"].get("observation_units", [])}
    variable_keys = {record["record_key"] for record in files["phenotyping"].get("observation_variables", [])}
    run_keys = {record["record_key"] for record in files["gwas"].get("runs", [])}
    qtl_keys = {record["record_key"] for record in files["qtls"].get("qtls", [])}

    for unit in files["observations"].get("observation_units", []):
        _require_ref("observation_units", unit, "study_key", study_keys, errors)
        _require_ref("observation_units", unit, "germplasm_key", germplasm_keys, errors)
    for obs in files["observations"].get("observations", []):
        _require_ref("observations", obs, "observation_unit_key", unit_keys, errors)
        _require_ref("observations", obs, "observation_variable_key", variable_keys, errors)
        _require_ref("observations", obs, "germplasm_key", germplasm_keys, errors)
        _require_ref("observations", obs, "study_key", study_keys, errors)
    for result in files["gwas"].get("results", []):
        _require_ref("gwas_results", result, "run_key", run_keys, errors)
    for candidate in files["qtls"].get("candidate_genes", []):
        _require_ref("candidate_genes", candidate, "qtl_key", qtl_keys, errors)


def _validate_business_rules(files: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
    studies_by_trial = {}
    for study in files["trials"].get("studies", []):
        studies_by_trial.setdefault(study["trial_key"], 0)
        studies_by_trial[study["trial_key"]] += 1
    for trial in files["trials"].get("trials", []):
        if studies_by_trial.get(trial["record_key"], 0) < 1:
            errors.append(_issue("trials", "trial has no study", trial))

    variable_by_key = {
        variable["record_key"]: variable
        for variable in files["phenotyping"].get("observation_variables", [])
    }
    missing_geo = 0
    for obs in files["observations"].get("observations", []):
        variable = variable_by_key.get(obs["observation_variable_key"], {})
        _validate_observation_value(obs, variable, errors)
        if not obs.get("geo_coordinates"):
            missing_geo += 1
    obs_count = len(files["observations"].get("observations", []))
    if obs_count and missing_geo / obs_count > 0.1:
        warnings.append({"table": "observations", "issue": "More than 10% of observations have no geo_coordinates", "severity": "low"})

    for result in files["gwas"].get("results", []):
        p_value = result.get("p_value")
        if p_value is None or not (0 < p_value <= 1):
            errors.append(_issue("gwas_results", "p_value must be in (0, 1]", result))
    for qtl in files["qtls"].get("qtls", []):
        start = qtl.get("start_position")
        peak = qtl.get("peak_position")
        end = qtl.get("end_position")
        if not (start <= peak <= end):
            errors.append(_issue("qtls", "QTL interval is not chronological", qtl))


def _validate_observation_value(
    obs: dict[str, Any],
    variable: dict[str, Any],
    errors: list[dict[str, Any]],
) -> None:
    value = obs.get("value")
    trait = variable.get("trait_name")
    valid_values = variable.get("valid_values") or {}
    data_type = variable.get("data_type", "Numerical")
    if data_type == "Nominal":
        categories = {str(item) for item in valid_values.get("categories", [])}
        if categories and str(value) not in categories:
            errors.append(_issue("observations", f"{trait} not in nominal categories", obs))
        return

    numeric_value = _float_value(value)
    if numeric_value is None:
        errors.append(_issue("observations", "observation value is not numeric", obs))
        return
    minimum = _float_value(valid_values.get("min"))
    maximum = _float_value(valid_values.get("max"))
    if minimum is not None and numeric_value < minimum:
        errors.append(_issue("observations", f"{trait} below valid minimum", obs))
    if maximum is not None and numeric_value > maximum:
        errors.append(_issue("observations", f"{trait} above valid maximum", obs))
    if trait in {"Grain Yield", "Seed Yield", "Fruit Yield", "Plant Height", "Days to Flowering"} and numeric_value <= 0:
        errors.append(_issue("observations", f"{trait} must be positive", obs))


def _validate_trait_coverage(files: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    by_crop: dict[str, set[str]] = {}
    for variable in files["phenotyping"].get("observation_variables", []):
        crop_name = variable.get("common_crop_name")
        trait_name = variable.get("trait_name")
        if crop_name and trait_name:
            by_crop.setdefault(str(crop_name), set()).add(str(trait_name))
    for crop_name, trait_names in by_crop.items():
        if len(trait_names) < 5:
            errors.append(
                {
                    "table": "observation_variables",
                    "issue": f"{crop_name} has fewer than 5 traits",
                    "record_key": crop_name,
                    "severity": "high",
                }
            )


def _validate_real_data_ratio(stats: dict[str, Any], warnings: list[dict[str, Any]]) -> None:
    total = stats.get("total_records", 0)
    if not total:
        return
    real_ratio = stats.get("real_records", 0) / total
    if real_ratio < 0.05:
        warnings.append(
            {
                "table": "pipeline",
                "issue": f"Real data ratio is {real_ratio:.1%}; synthetic fallback dominates this run",
                "severity": "medium",
            }
        )


def _require_ref(table: str, record: dict[str, Any], field: str, valid: set[str], errors: list[dict[str, Any]]) -> None:
    if record.get(field) not in valid:
        errors.append(_issue(table, f"unresolved reference: {field}", record))


def _float_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _issue(table: str, issue: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "table": table,
        "issue": issue,
        "record_key": record.get("record_key") or record.get("observation_db_id") or record.get("qtl_db_id"),
        "severity": "high",
    }
