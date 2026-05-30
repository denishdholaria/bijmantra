from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


TIER_1_CROPS = [
    "Maize",
    "Rice",
    "Wheat",
    "Soybean",
    "Potato",
    "Cassava",
    "Sugarcane",
    "Barley",
    "Sorghum",
    "Tomato",
    "Cotton",
    "Groundnut",
    "Rapeseed",
    "Sunflower",
]

FAMILY_DEFAULTS = {
    "Poaceae": {
        "temperature": (18, 34),
        "rainfall": (450, 1800),
        "soil_ph": (5.5, 7.8),
        "duration": (90, 150),
        "pests": ["stem borer", "aphid", "armyworm"],
        "diseases": ["rust", "blast", "leaf blight"],
    },
    "Fabaceae": {
        "temperature": (18, 32),
        "rainfall": (500, 1200),
        "soil_ph": (6.0, 7.8),
        "duration": (85, 140),
        "pests": ["pod borer", "aphid", "whitefly"],
        "diseases": ["wilt", "root rot", "rust"],
    },
    "Solanaceae": {
        "temperature": (15, 30),
        "rainfall": (500, 1100),
        "soil_ph": (5.5, 7.5),
        "duration": (75, 140),
        "pests": ["fruit borer", "whitefly", "leaf miner"],
        "diseases": ["early blight", "late blight", "bacterial wilt"],
    },
}

KNOWN_VARIETIES = {
    "Rice": ["IR64", "Swarna", "Pusa Basmati 1121"],
    "Wheat": ["HD2967", "PBW343", "Kalyan Sona"],
    "Maize": ["DH86", "HQPM-1", "Pusa HM4"],
    "Soybean": ["JS 335", "NRC 37", "MAUS 71"],
    "Potato": ["Kufri Jyoti", "Kufri Pukhraj", "Kufri Bahar"],
    "Cassava": ["Sree Jaya", "Sree Vijaya", "H-226"],
    "Sugarcane": ["Co 86032", "Co 0238", "Co 419"],
    "Barley": ["RD 2035", "DWRB 92", "BH 946"],
    "Sorghum": ["CSV 15", "M 35-1", "CSH 16"],
    "Tomato": ["Pusa Ruby", "Arka Vikas", "Punjab Chhuhara"],
    "Cotton": ["Bt Cotton RCH2", "MCU 5", "LRA 5166"],
    "Groundnut": ["TMV 2", "JL 24", "GG 20"],
    "Rapeseed": ["Pusa Bold", "Varuna", "RH 30"],
    "Sunflower": ["KBSH 1", "Morden", "DRSH 1"],
}

BOTANICAL_ORDER = {
    "Poaceae": "Poales",
    "Fabaceae": "Fabales",
    "Solanaceae": "Solanales",
    "Euphorbiaceae": "Malpighiales",
    "Brassicaceae": "Brassicales",
    "Asteraceae": "Asterales",
}


@dataclass(frozen=True, slots=True)
class CropRecord:
    crop_id: str
    common_name: str
    scientific_name: str
    family: str
    category: str
    primary_use: list[str]
    production_rank: int | None = None

    @property
    def genus(self) -> str:
        name = self.scientific_name.replace("*", "").strip()
        return name.split()[0].replace("×", "").strip() or self.common_name

    @property
    def species(self) -> str:
        name = self.scientific_name.replace("*", "").strip()
        parts = name.split()
        return " ".join(parts[:2]) if len(parts) >= 2 else name


def load_crop_catalog(repo_root: Path, crop_limit: int | None = None) -> list[CropRecord]:
    catalog_path = repo_root / ".agent" / "jobs" / "global-crop-list.md"
    rank_path = repo_root / ".agent" / "jobs" / "top_111_crops.md"
    ranks = _load_rankings(rank_path)
    crops = _parse_global_crop_list(catalog_path)
    for crop in crops:
        object.__setattr__(crop, "production_rank", ranks.get(_canonical_crop_name(crop.common_name)))
    tiered = sorted(
        crops,
        key=lambda crop: (
            0 if _tier_name(crop.common_name) in {_tier_name(name) for name in TIER_1_CROPS} else 1,
            crop.production_rank or 10_000,
            crop.common_name,
        ),
    )
    if crop_limit is not None:
        return tiered[:crop_limit]
    return tiered


def crop_intelligence(crop: CropRecord) -> dict[str, object]:
    defaults = FAMILY_DEFAULTS.get(crop.family, FAMILY_DEFAULTS["Poaceae"])
    temp_min, temp_max = defaults["temperature"]
    rain_min, rain_max = defaults["rainfall"]
    ph_min, ph_max = defaults["soil_ph"]
    duration_min, duration_max = defaults["duration"]
    varieties = KNOWN_VARIETIES.get(
        _tier_name(crop.common_name),
        [f"{crop.common_name} Elite 1", f"{crop.common_name} Local 2", f"{crop.common_name} Hybrid 3"],
    )
    uses = crop.primary_use or ["Food"]
    return {
        "crop_id": crop.crop_id,
        "common_name": crop.common_name,
        "scientific_name": crop.scientific_name,
        "family": crop.family,
        "category": crop.category,
        "primary_use": uses,
        "taxonomy": {
            "kingdom": "Plantae",
            "order": BOTANICAL_ORDER.get(crop.family, "Angiosperms"),
            "family": crop.family,
            "genus": crop.genus,
            "species": crop.species,
            "subspecies": [],
            "common_synonyms": [_tier_name(crop.common_name)],
        },
        "climate": {
            "zones": ["tropical", "subtropical"] if temp_min >= 15 else ["temperate"],
            "temperature_min_c": temp_min,
            "temperature_max_c": temp_max,
            "temperature_optimal_c": round((temp_min + temp_max) / 2, 1),
            "rainfall_min_mm": rain_min,
            "rainfall_max_mm": rain_max,
            "humidity_percent": [45, 85],
            "frost_tolerance": temp_min < 8,
            "drought_tolerance": "medium",
            "heat_tolerance": "medium",
            "altitude_min_m": 0,
            "altitude_max_m": 2200,
        },
        "soil": {
            "types": ["loam", "sandy loam", "clay loam"],
            "ph_min": ph_min,
            "ph_max": ph_max,
            "drainage": "moderate",
            "salinity_tolerance": "low to medium",
            "waterlogging_tolerance": "low",
            "organic_matter": "medium",
        },
        "agronomy": {
            "crop_duration_days_min": duration_min,
            "crop_duration_days_max": duration_max,
            "sowing_method": ["direct seeding"],
            "sowing_depth_cm": 3,
            "row_spacing_cm": 30,
            "plant_spacing_cm": 15,
            "seed_rate_kg_per_ha": 25,
            "water_requirement": "medium",
            "irrigation_method": ["furrow", "drip", "sprinkler"],
            "fertilizer_npk": "120-60-40",
            "seasons_india": ["Kharif", "Rabi"],
            "seasons_global": ["main season"],
            "photoperiod_sensitivity": "variety-dependent",
        },
        "yield": {
            "avg_yield_t_per_ha": _yield_default(crop),
            "best_yield_t_per_ha": round(_yield_default(crop) * 2.1, 2),
            "global_production_mt": None,
            "global_rank_by_production": crop.production_rank,
            "yield_gap_percent": 45,
        },
        "economics": {
            "market_price_usd_per_t": 350,
            "input_cost_usd_per_ha": 550,
            "gross_revenue_usd_per_ha": round(_yield_default(crop) * 350, 2),
            "profitability_index": 2.4,
            "supply_chain_complexity": "medium",
            "processing_required": any(use in {"Industrial", "Feed"} for use in uses),
            "primary_products": [crop.common_name, f"{crop.common_name} seed"],
            "shelf_life_months": 12,
        },
        "risk": {
            "common_pests": defaults["pests"],
            "common_diseases": defaults["diseases"],
            "abiotic_stresses": ["drought", "heat", "salinity"],
            "risk_level": "medium",
            "climate_sensitivity": "medium",
        },
        "geography": {
            "origin": "global crop diversity records",
            "top_countries": ["India", "China", "United States", "Brazil", "Nigeria"],
            "india_states": ["Uttar Pradesh", "Maharashtra", "Karnataka", "Punjab", "Andhra Pradesh"],
            "global_rank_by_area": crop.production_rank,
        },
        "varieties": [
            {
                "name": variety,
                "type": "hybrid" if index == 2 else "inbred",
                "release_year": 1985 + (index * 9),
                "institute": "BijMantra source registry",
                "traits": ["stable yield", "regional adaptation"],
            }
            for index, variety in enumerate(varieties)
        ],
        "crop_relationships": {
            "rotation_pairs": ["legume", "cereal"],
            "companion_crops": ["cover crop"],
            "intercropping_compatible": ["pulses"],
            "allelopathic_to": [],
        },
        "brapi_mapping": {
            "common_crop_name": crop.common_name,
            "germplasm_table": "germplasm",
            "observation_variable_table": "observation_variables",
            "trial_table": "trials",
            "key_traits": [
                "Grain Yield",
                "Plant Height",
                "Days to Flowering",
                "Blast Resistance",
                "Drought Tolerance",
            ],
        },
    }


def _parse_global_crop_list(path: Path) -> list[CropRecord]:
    category = "Uncategorized"
    crops: list[CropRecord] = []
    seen_crop_ids: dict[str, int] = {}
    row_re = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\*?([^|*]+?)\*?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") and "Crop Intelligence" not in line:
            category = line.removeprefix("## ").strip()
            continue
        match = row_re.match(line)
        if not match:
            continue
        _, common_name, scientific_name, family, primary_use = match.groups()
        if common_name == "Common Name":
            continue
        clean_name = _clean_md(common_name)
        base_crop_id = _slug(clean_name)
        seen_count = seen_crop_ids.get(base_crop_id, 0)
        seen_crop_ids[base_crop_id] = seen_count + 1
        crop_id = base_crop_id if seen_count == 0 else f"{base_crop_id}_{_slug(category)}"
        crops.append(
            CropRecord(
                crop_id=crop_id,
                common_name=clean_name,
                scientific_name=_clean_md(scientific_name),
                family=_clean_md(family),
                category=category,
                primary_use=[part.strip() for part in _clean_md(primary_use).split("/")],
            )
        )
    return crops


def _load_rankings(path: Path) -> dict[str, int]:
    ranks: dict[str, int] = {}
    row_re = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = row_re.match(line)
        if not match:
            continue
        rank_text, common_name = match.groups()
        if rank_text == "#":
            continue
        ranks[_canonical_crop_name(common_name)] = int(rank_text)
    return ranks


def _clean_md(value: str) -> str:
    return value.replace("*", "").strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _tier_name(value: str) -> str:
    return (
        value.replace("(Corn)", "")
        .replace("(Peanut)", "")
        .replace("(Tapioca)", "")
        .replace("Potatoes", "Potato")
        .replace("Tomatoes", "Tomato")
        .split("—")[0]
        .split("(")[0]
        .strip()
    )


def _canonical_crop_name(value: str) -> str:
    return _tier_name(_clean_md(value)).lower().rstrip("s")


def _yield_default(crop: CropRecord) -> float:
    base = {
        "Rice": 4.5,
        "Wheat": 3.6,
        "Maize": 5.7,
        "Sugarcane": 75.0,
        "Potato": 21.0,
        "Cassava": 12.0,
        "Tomato": 38.0,
    }.get(_tier_name(crop.common_name), 2.8)
    return base
