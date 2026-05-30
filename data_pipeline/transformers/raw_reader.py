from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

from data_pipeline.io import read_json


class RawDataReader:
    """Reads wrapped fetcher output and returns transformer-friendly structures."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir

    def gbif_taxonomy(self) -> dict[str, dict[str, Any]]:
        records = self._read_data("gbif_taxonomy.json", default=[])
        if isinstance(records, dict):
            records = records.get("results") or records.get("data") or []
        result: dict[str, dict[str, Any]] = {}
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                continue
            keys = {
                record.get("_query_name"),
                record.get("scientificName"),
                record.get("canonicalName"),
                record.get("species"),
            }
            for key in keys:
                if key:
                    result[_normalize_name(str(key))] = record
        return result

    def faostat_yield_baselines(self) -> dict[str, dict[str, Any]]:
        records = self._read_data("faostat_yield_baselines.json", default=[])
        if isinstance(records, dict):
            records = records.get("data") or records.get("rows") or []
        grouped: dict[str, list[float]] = {}
        units: dict[str, str] = {}
        for row in records if isinstance(records, list) else []:
            if not isinstance(row, dict):
                continue
            item = _first_present(row, ("Item", "item", "crop", "Item Name", "itemName"))
            value = _as_float(_first_present(row, ("Value", "value", "yield", "YLD")))
            if not item or value is None:
                continue
            unit = str(_first_present(row, ("Unit", "unit"), "") or "")
            kg_per_ha = _yield_to_kg_per_ha(value, unit)
            crop_key = _normalize_crop(str(item))
            grouped.setdefault(crop_key, []).append(kg_per_ha)
            units[crop_key] = "kg/ha"

        baselines: dict[str, dict[str, Any]] = {}
        for crop_key, values in grouped.items():
            if not values:
                continue
            mean = statistics.fmean(values)
            std = statistics.pstdev(values) if len(values) > 1 else max(mean * 0.12, 1.0)
            baselines[crop_key] = {
                "mean": round(mean, 4),
                "std": round(max(std, mean * 0.05, 1.0), 4),
                "unit": units.get(crop_key, "kg/ha"),
                "count": len(values),
            }
        return baselines

    def crop_ontology_traits(self, crop_id: str | None = None) -> list[dict[str, Any]]:
        if crop_id:
            candidates = [self.raw_dir / f"crop_ontology_{crop_id}.json"]
        else:
            candidates = sorted(self.raw_dir.glob("crop_ontology_*.json"))
        traits: list[dict[str, Any]] = []
        for path in candidates:
            payload = self._read_path(path, default={})
            data = _unwrap(payload)
            if isinstance(data, dict):
                data = data.get("result", {}).get("data") if isinstance(data.get("result"), dict) else data.get("data", data)
            if isinstance(data, list):
                traits.extend(record for record in data if isinstance(record, dict))
            elif isinstance(data, dict) and data.get("traits"):
                traits.extend(record for record in data["traits"] if isinstance(record, dict))
        return traits

    def brapi_germplasm(self) -> list[dict[str, Any]]:
        payload = self._read_data("brapi_test_server_germplasm.json", default={})
        return _brapi_result_data(payload)

    def brapi_variables(self) -> list[dict[str, Any]]:
        payload = self._read_data("brapi_test_server_variables.json", default={})
        return _brapi_result_data(payload)

    def fetch_errors(self) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for path in sorted(self.raw_dir.glob("*_error.json")):
            payload = self._read_path(path, default={})
            errors.append(
                {
                    "source": payload.get("source") or payload.get("metadata", {}).get("source") or path.stem.removesuffix("_error"),
                    "error": payload.get("error"),
                    "raw_path": str(path),
                }
            )
        return errors

    def _read_data(self, filename: str, default: Any) -> Any:
        return _unwrap(self._read_path(self.raw_dir / filename, default=default))

    def _read_path(self, path: Path, default: Any) -> Any:
        return read_json(path, default=default)


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload and "metadata" in payload:
        return payload["data"]
    return payload


def _brapi_result_data(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        result = payload.get("result")
        if isinstance(result, dict) and isinstance(result.get("data"), list):
            return [record for record in result["data"] if isinstance(record, dict)]
        data = payload.get("data")
        if isinstance(data, list):
            return [record for record in data if isinstance(record, dict)]
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    return []


def _first_present(row: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _yield_to_kg_per_ha(value: float, unit: str) -> float:
    normalized = unit.lower().replace(" ", "")
    if normalized in {"hg/ha", "100g/ha"}:
        return value / 10.0
    if normalized in {"t/ha", "tonnes/ha", "tonne/ha"}:
        return value * 1000.0
    return value


def _normalize_name(value: str) -> str:
    return " ".join(value.replace("×", "x").lower().split())


def _normalize_crop(value: str) -> str:
    return (
        _normalize_name(value)
        .replace("maize (corn)", "maize")
        .replace("rice, paddy", "rice")
        .replace("soybeans", "soybean")
        .replace("potatoes", "potato")
        .replace("tomatoes", "tomato")
    )
