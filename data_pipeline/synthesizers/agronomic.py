from __future__ import annotations

import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from data_pipeline.transformers.raw_reader import RawDataReader


_FAOSTAT_CACHE: dict[str, dict[str, Any]] = {}

CROP_YIELD_BASE = {
    "Rice": 5200.0,
    "Wheat": 4300.0,
    "Maize": 6500.0,
    "Soybean": 2600.0,
    "Potato": 23000.0,
    "Cassava": 15000.0,
    "Sugarcane": 78000.0,
    "Tomato": 42000.0,
    "Banana": 30000.0,
    "Mango": 12000.0,
}


def load_faostat_baselines(raw_dir: Path) -> None:
    _FAOSTAT_CACHE.clear()
    _FAOSTAT_CACHE.update(RawDataReader(raw_dir).faostat_yield_baselines())


def synthesize_observation_value(
    trait_name: str,
    *,
    crop_name: str,
    germplasm_index: int,
    study_index: int = 0,
    seed: int = 1729,
    valid_min: float | None = None,
    valid_max: float | None = None,
    nominal_values: list[str] | tuple[str, ...] | None = None,
    data_type: str = "Numerical",
) -> float | int | str:
    rng = random.Random(f"{seed}:{crop_name}:{trait_name}:{germplasm_index}:{study_index}")
    if data_type == "Nominal":
        return _synth_nominal(rng, tuple(nominal_values or ("standard",)))
    if data_type == "Ordinal" or trait_name in {
        "Blast Resistance",
        "Drought Tolerance",
        "Drought Tolerance Score",
    }:
        return _synth_ordinal(rng, valid_min or 1, valid_max or 9)

    synthesizer = TRAIT_SYNTHESIZERS.get(trait_name)
    if synthesizer:
        value = synthesizer(rng, crop_name, germplasm_index)
    else:
        value = _synth_generic(rng, valid_min, valid_max)
    if valid_min is not None and valid_max is not None:
        value = _clip(float(value), valid_min, valid_max)
    return round(float(value), 2)


def synthetic_method_for_trait(trait_name: str, crop_name: str) -> str:
    if trait_name in {"Grain Yield", "Seed Yield"} and _yield_cache_entry(crop_name):
        return "faostat_anchored_normal_distribution"
    if trait_name in TRAIT_SYNTHESIZERS:
        return "category_trait_distribution"
    return "bounded_uniform_distribution"


def _yield_base_for_crop(crop_name: str) -> tuple[float, float]:
    entry = _yield_cache_entry(crop_name)
    if entry:
        return float(entry["mean"]), float(entry["std"])
    base = CROP_YIELD_BASE.get(_simple_crop_name(crop_name), 3600.0)
    return base, max(base * 0.18, 1.0)


def _yield_cache_entry(crop_name: str) -> dict[str, Any] | None:
    normalized = _normalize_crop(crop_name)
    return _FAOSTAT_CACHE.get(normalized) or _FAOSTAT_CACHE.get(_normalize_crop(_simple_crop_name(crop_name)))


def _synth_grain_yield(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    mean, std = _yield_base_for_crop(crop_name)
    vigor = 0.9 + (germplasm_index % 5) * 0.04
    return max(300.0, rng.gauss(mean * vigor, std * 0.55))


def _synth_plant_height(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    base = 65.0 + (germplasm_index % 5) * 8.0
    if _simple_crop_name(crop_name) in {"Sugarcane", "Banana"}:
        base = 240.0
    return base + rng.gauss(0, 10)


def _synth_days(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    base = 95.0 + math.sin(germplasm_index) * 14.0
    if _simple_crop_name(crop_name) in {"Cassava", "Sugarcane", "Mango", "Banana"}:
        base = 240.0
    return base + rng.gauss(0, 6)


def _synth_fruit_yield(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    base = {
        "Tomato": 40.0,
        "Mango": 12.0,
        "Banana": 30.0,
        "Papaya": 45.0,
        "Apple": 25.0,
    }.get(_simple_crop_name(crop_name), 18.0)
    return base * (0.82 + (germplasm_index % 4) * 0.07) + rng.gauss(0, base * 0.08)


def _synth_root_yield(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    base = {"Potato": 22.0, "Cassava": 15.0, "Sweet Potato": 18.0, "Yam": 14.0}.get(
        _simple_crop_name(crop_name),
        16.0,
    )
    return base * (0.85 + (germplasm_index % 4) * 0.08) + rng.gauss(0, base * 0.1)


def _synth_brix(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    name = _simple_crop_name(crop_name)
    if name in {"Sugarcane", "Sugar Beet"}:
        base = 18.0
    elif name in {"Tomato", "Cucumber", "Pumpkin", "Zucchini", "Okra"}:
        base = 5.0
    else:
        base = 13.0
    return base + (germplasm_index % 3) * 0.45 + rng.gauss(0, 0.9)


def _synth_oil_content(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    name = _simple_crop_name(crop_name)
    if name in {"Almond", "Walnut", "Pistachio", "Hazelnut", "Macadamia", "Pecan"}:
        base = 55.0
    elif name in {"Groundnut", "Sunflower", "Rapeseed", "Sesame", "Safflower"}:
        base = 42.0
    else:
        base = 24.0
    return base + (germplasm_index % 4) * 1.2 + rng.gauss(0, 2.5)


def _synth_protein_content(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    name = _simple_crop_name(crop_name)
    if name in {"Soybean", "Chickpea", "Lentil", "Dry Beans", "Pea"}:
        base = 25.0
    elif name in {"Rice", "Wheat", "Maize", "Barley"}:
        base = 11.0
    elif name in {"Almond", "Walnut", "Cashew", "Pistachio"}:
        base = 18.0
    else:
        base = 14.0
    return base + (germplasm_index % 3) * 0.6 + rng.gauss(0, 1.2)


def _synth_fiber_length(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    name = _simple_crop_name(crop_name)
    if name == "Cotton":
        base = 30.0
    elif name == "Jute":
        base = 2200.0
    elif name == "Hemp":
        base = 1500.0
    else:
        base = 40.0
    return base + (germplasm_index % 3) * base * 0.03 + rng.gauss(0, max(base * 0.05, 1.0))


def _synth_essential_oil(rng: random.Random, crop_name: str, germplasm_index: int) -> float:
    base = {
        "Mint": 1.2,
        "Basil": 0.8,
        "Rosemary": 1.6,
        "Thyme": 1.4,
        "Lavender": 2.0,
        "Lemongrass": 0.9,
    }.get(_simple_crop_name(crop_name), 1.0)
    return base + (germplasm_index % 3) * 0.15 + rng.gauss(0, 0.18)


def _synth_ordinal(rng: random.Random, valid_min: float, valid_max: float) -> int:
    return rng.randint(int(valid_min), int(valid_max))


def _synth_nominal(rng: random.Random, nominal_values: tuple[str, ...]) -> str:
    return rng.choice(nominal_values)


def _synth_generic(rng: random.Random, valid_min: float | None, valid_max: float | None) -> float:
    minimum = 0.0 if valid_min is None else valid_min
    maximum = 100.0 if valid_max is None else valid_max
    return rng.uniform(minimum, maximum)


def _clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _simple_crop_name(crop_name: str) -> str:
    return crop_name.split("—")[0].split("(")[0].strip()


def _normalize_crop(crop_name: str) -> str:
    return " ".join(_simple_crop_name(crop_name).lower().rstrip("s").split())


TRAIT_SYNTHESIZERS: dict[str, Callable[[random.Random, str, int], float]] = {
    "Grain Yield": _synth_grain_yield,
    "Seed Yield": _synth_grain_yield,
    "Nut Yield": _synth_grain_yield,
    "Fiber Yield": _synth_grain_yield,
    "Plant Height": _synth_plant_height,
    "Days to Flowering": _synth_days,
    "Days to Heading": _synth_days,
    "Days to Maturity": _synth_days,
    "Days to Harvest": _synth_days,
    "Days to First Harvest": _synth_days,
    "Days to First Cut": _synth_days,
    "Days to Full Bloom": _synth_days,
    "Fresh Root Yield": _synth_root_yield,
    "Root Weight": _synth_root_yield,
    "Bulb/Root Yield": _synth_root_yield,
    "Cane/Beet Yield": _synth_root_yield,
    "Fruit Yield": _synth_fruit_yield,
    "Marketable Yield": _synth_fruit_yield,
    "Fresh Herb Yield": _synth_fruit_yield,
    "Fresh Biomass Yield": _synth_fruit_yield,
    "Total Soluble Solids / Brix": _synth_brix,
    "Brix": _synth_brix,
    "Oil Content": _synth_oil_content,
    "Protein Content": _synth_protein_content,
    "Crude Protein Content": _synth_protein_content,
    "Fiber Length": _synth_fiber_length,
    "Essential Oil Content": _synth_essential_oil,
    "Essential Oil Yield": _synth_essential_oil,
}
