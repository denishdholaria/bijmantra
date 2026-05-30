from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TraitDef:
    trait_name: str
    trait_class: str
    scale_name: str
    unit: str | None
    data_type: str
    valid_min: float | None
    valid_max: float | None
    ontology_db_id: str | None
    method_name: str
    method_description: str
    nominal_values: tuple[str, ...] = ()


def _trait(
    trait_name: str,
    trait_class: str,
    scale_name: str,
    unit: str | None,
    data_type: str,
    valid_min: float | None,
    valid_max: float | None,
    method_name: str,
    method_description: str,
    ontology_db_id: str | None = None,
    nominal_values: tuple[str, ...] = (),
) -> TraitDef:
    return TraitDef(
        trait_name=trait_name,
        trait_class=trait_class,
        scale_name=scale_name,
        unit=unit,
        data_type=data_type,
        valid_min=valid_min,
        valid_max=valid_max,
        ontology_db_id=ontology_db_id,
        method_name=method_name,
        method_description=method_description,
        nominal_values=nominal_values,
    )


def _score_trait(
    name: str,
    trait_class: str,
    method: str = "Visual field score",
    method_description: str = "Ordinal stress or resistance score.",
    ontology_db_id: str | None = None,
) -> TraitDef:
    return _trait(
        name,
        trait_class,
        "1-9 scale",
        None,
        "Ordinal",
        1,
        9,
        method,
        method_description,
        ontology_db_id,
    )


def _nominal_trait(name: str, trait_class: str, values: tuple[str, ...]) -> TraitDef:
    return _trait(name, trait_class, "category", None, "Nominal", None, None, "Visual category", "Observed categorical class.", nominal_values=values)


CATEGORY_TRAIT_REGISTRY: dict[str, tuple[TraitDef, ...]] = {
    "Cereals & Grains": (
        _trait("Grain Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 500, 12000, "Plot harvest adjusted to standard moisture", "Harvested plot grain weight converted to kg/ha.", "CO_321:0001218"),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 10, 450, "Ground-to-apex field measurement", "Plant height measured from ground level to apex.", "CO_321:0000994"),
        _trait("Days to Heading", "Phenological", "days", "days", "Numerical", 20, 220, "Days from sowing to heading", "Days from sowing to 50 percent heading.", "CO_321:0000183"),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 60, 260, "Days from sowing to physiological maturity", "Days from sowing to crop maturity."),
        _trait("Thousand Grain Weight", "Grain Quality", "g", "g", "Numerical", 5, 80, "Clean seed sample weighing", "Weight of 1000 filled grains."),
        _score_trait("Blast Resistance", "Biotic Stress", "Visual disease score", "Leaf or panicle blast severity score.", "CO_321:0000175"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress", "Managed stress score", "Drought response under managed stress.", "CO_321:0000433"),
        _score_trait("Lodging Score", "Abiotic Stress"),
        _trait("Panicle Length", "Morphological", "cm", "cm", "Numerical", 5, 60, "Panicle measurement", "Length from panicle base to tip."),
        _trait("Tiller Number", "Morphological", "count", "count", "Numerical", 1, 80, "Tiller count per plant", "Number of productive tillers."),
    ),
    "Pulses & Legumes": (
        _trait("Seed Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 300, 7000, "Plot harvest", "Clean seed yield converted to kg/ha."),
        _trait("Days to Flowering", "Phenological", "days", "days", "Numerical", 20, 150, "Days to 50 percent flowering", "Days from sowing to flowering."),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 55, 220, "Days to maturity", "Days from sowing to maturity."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 10, 250, "Plant height measurement", "Ground-to-apex plant height."),
        _trait("100 Seed Weight", "Seed Quality", "g", "g", "Numerical", 1, 100, "Seed sample weighing", "Weight of 100 clean seeds."),
        _trait("Pod Number per Plant", "Yield Component", "count", "count", "Numerical", 1, 300, "Pod count", "Mature pods counted per plant."),
        _trait("Seeds per Pod", "Yield Component", "count", "count", "Numerical", 1, 15, "Seed count per pod", "Mean number of seeds per pod."),
        _score_trait("Wilt Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _trait("Protein Content", "Quality", "%", "%", "Numerical", 10, 40, "Protein assay", "Seed protein percentage."),
    ),
    "Oilseeds": (
        _trait("Seed Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 300, 8000, "Plot harvest", "Clean seed yield converted to kg/ha."),
        _trait("Oil Content", "Quality", "%", "%", "Numerical", 15, 60, "Oil extraction assay", "Seed oil percentage."),
        _trait("Protein Content", "Quality", "%", "%", "Numerical", 8, 45, "Protein assay", "Seed protein percentage."),
        _trait("Days to Flowering", "Phenological", "days", "days", "Numerical", 25, 160, "Days to flowering", "Days from sowing to flowering."),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 70, 220, "Days to maturity", "Days from sowing to maturity."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 20, 350, "Plant height measurement", "Ground-to-apex plant height."),
        _trait("1000 Seed Weight", "Seed Quality", "g", "g", "Numerical", 2, 1000, "Seed sample weighing", "Weight of 1000 clean seeds."),
        _trait("Fatty Acid Profile - Oleic Acid", "Quality", "%", "%", "Numerical", 10, 90, "Fatty acid assay", "Oleic acid share of seed oil."),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _score_trait("Aphid Resistance", "Biotic Stress"),
    ),
    "Roots & Tubers": (
        _trait("Fresh Root Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 5, 90, "Fresh root harvest", "Fresh root or tuber yield."),
        _trait("Dry Matter Content", "Quality", "%", "%", "Numerical", 10, 55, "Dry matter assay", "Dry matter percentage."),
        _trait("Starch Content", "Quality", "%", "%", "Numerical", 5, 45, "Starch assay", "Root or tuber starch percentage."),
        _trait("Days to Harvest", "Phenological", "days", "days", "Numerical", 60, 420, "Days from planting to harvest", "Crop duration to harvest."),
        _trait("Root Number per Plant", "Yield Component", "count", "count", "Numerical", 1, 40, "Root count", "Storage roots counted per plant."),
        _trait("Root Weight", "Yield Component", "kg", "kg", "Numerical", 0.05, 10, "Root weighing", "Mean storage root or tuber weight."),
        _nominal_trait("Skin Color", "Quality", ("white", "yellow", "red", "brown", "purple")),
        _nominal_trait("Flesh Color", "Quality", ("white", "cream", "yellow", "orange", "purple")),
        _score_trait("Late Blight Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
    ),
    "Sugar Crops": (
        _trait("Cane/Beet Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 10, 160, "Harvest yield", "Fresh cane or beet yield."),
        _trait("Sucrose Content", "Quality", "%", "%", "Numerical", 8, 24, "Sucrose assay", "Recoverable sucrose percentage."),
        _trait("Brix", "Quality", "degree Brix", "degree Brix", "Numerical", 8, 24, "Refractometer reading", "Total soluble solids."),
        _trait("Purity", "Quality", "%", "%", "Numerical", 50, 100, "Juice purity calculation", "Sucrose purity percentage."),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 120, 540, "Days to harvest maturity", "Crop duration to maturity."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 20, 500, "Plant height measurement", "Plant height at harvest."),
        _score_trait("Smut Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
    ),
    "Fruits - Tropical & Subtropical": (
        _trait("Fruit Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 2, 100, "Marketable fruit harvest", "Marketable fruit yield."),
        _trait("Average Fruit Weight", "Yield Component", "g", "g", "Numerical", 5, 5000, "Fruit weighing", "Mean fruit weight."),
        _trait("Fruit Length", "Morphological", "cm", "cm", "Numerical", 1, 80, "Fruit length measurement", "Fruit length."),
        _trait("Fruit Diameter", "Morphological", "cm", "cm", "Numerical", 1, 40, "Fruit diameter measurement", "Fruit diameter."),
        _trait("Total Soluble Solids / Brix", "Quality", "degree Brix", "degree Brix", "Numerical", 3, 30, "Refractometer reading", "Total soluble solids."),
        _trait("Titratable Acidity", "Quality", "%", "%", "Numerical", 0.05, 5, "Acidity titration", "Titratable acidity percentage."),
        _trait("Days to First Harvest", "Phenological", "days", "days", "Numerical", 45, 900, "Days to first harvest", "Days from planting to first harvest."),
        _trait("Shelf Life", "Quality", "days", "days", "Numerical", 1, 120, "Ambient shelf-life observation", "Days until market quality loss."),
        _score_trait("Anthracnose Resistance", "Biotic Stress"),
        _nominal_trait("Fruit Skin Color", "Quality", ("green", "yellow", "orange", "red", "purple", "brown")),
    ),
    "Fruits - Temperate": (
        _trait("Fruit Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 2, 80, "Marketable fruit harvest", "Marketable fruit yield."),
        _trait("Average Fruit Weight", "Yield Component", "g", "g", "Numerical", 5, 800, "Fruit weighing", "Mean fruit weight."),
        _trait("Fruit Firmness", "Quality", "N", "N", "Numerical", 5, 120, "Penetrometer reading", "Fruit firmness."),
        _trait("Total Soluble Solids / Brix", "Quality", "degree Brix", "degree Brix", "Numerical", 5, 28, "Refractometer reading", "Total soluble solids."),
        _trait("Titratable Acidity", "Quality", "%", "%", "Numerical", 0.05, 4, "Acidity titration", "Titratable acidity percentage."),
        _trait("Days to Full Bloom", "Phenological", "days", "days", "Numerical", 30, 180, "Bloom date observation", "Days from season start to full bloom."),
        _trait("Days to Harvest", "Phenological", "days", "days", "Numerical", 80, 260, "Harvest date observation", "Days from bloom or season start to harvest."),
        _trait("Shelf Life", "Quality", "days", "days", "Numerical", 3, 240, "Storage shelf-life observation", "Days until market quality loss."),
        _score_trait("Scab Resistance", "Biotic Stress"),
        _score_trait("Frost Tolerance", "Abiotic Stress"),
    ),
    "Vegetables - Leafy": (
        _trait("Marketable Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 1, 80, "Marketable harvest", "Marketable leaf yield."),
        _trait("Days to Harvest", "Phenological", "days", "days", "Numerical", 20, 120, "Days to harvest", "Days from sowing to harvest."),
        _trait("Leaf Length", "Morphological", "cm", "cm", "Numerical", 2, 120, "Leaf length measurement", "Mean leaf length."),
        _trait("Leaf Width", "Morphological", "cm", "cm", "Numerical", 1, 80, "Leaf width measurement", "Mean leaf width."),
        _nominal_trait("Leaf Color", "Quality", ("light green", "green", "dark green", "purple", "red")),
        _score_trait("Bolting Resistance", "Abiotic Stress"),
        _score_trait("Downy Mildew Resistance", "Biotic Stress"),
        _score_trait("Tip Burn Resistance", "Abiotic Stress"),
        _trait("Dry Matter Content", "Quality", "%", "%", "Numerical", 3, 30, "Dry matter assay", "Dry matter percentage."),
        _trait("Nitrate Content", "Quality", "mg/kg", "mg/kg", "Numerical", 50, 6000, "Nitrate assay", "Leaf nitrate concentration."),
    ),
    "Vegetables - Fruiting": (
        _trait("Fruit Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 2, 120, "Marketable fruit harvest", "Marketable fruit yield."),
        _trait("Average Fruit Weight", "Yield Component", "g", "g", "Numerical", 5, 3000, "Fruit weighing", "Mean fruit weight."),
        _trait("Days to First Harvest", "Phenological", "days", "days", "Numerical", 35, 180, "Days to first harvest", "Days from sowing or transplanting to first harvest."),
        _trait("Fruit Length", "Morphological", "cm", "cm", "Numerical", 1, 120, "Fruit length measurement", "Fruit length."),
        _trait("Fruit Diameter", "Morphological", "cm", "cm", "Numerical", 1, 60, "Fruit diameter measurement", "Fruit diameter."),
        _trait("Total Soluble Solids / Brix", "Quality", "degree Brix", "degree Brix", "Numerical", 2, 18, "Refractometer reading", "Total soluble solids."),
        _nominal_trait("Fruit Color at Maturity", "Quality", ("green", "yellow", "orange", "red", "purple", "white")),
        _score_trait("Early Blight Resistance", "Biotic Stress"),
        _score_trait("Bacterial Wilt Resistance", "Biotic Stress"),
        _trait("Shelf Life", "Quality", "days", "days", "Numerical", 1, 60, "Shelf-life observation", "Days until market quality loss."),
    ),
    "Vegetables - Bulb & Root": (
        _trait("Bulb/Root Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 2, 100, "Marketable harvest", "Marketable bulb or root yield."),
        _trait("Average Bulb/Root Weight", "Yield Component", "g", "g", "Numerical", 5, 3000, "Bulb or root weighing", "Mean bulb or root weight."),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 35, 240, "Days to maturity", "Days from sowing to maturity."),
        _trait("Bulb Diameter", "Morphological", "cm", "cm", "Numerical", 1, 25, "Bulb diameter measurement", "Bulb diameter."),
        _trait("Dry Matter Content", "Quality", "%", "%", "Numerical", 5, 45, "Dry matter assay", "Dry matter percentage."),
        _score_trait("Pungency Score", "Quality"),
        _score_trait("Bolting Resistance", "Abiotic Stress"),
        _score_trait("Purple Blotch Resistance", "Biotic Stress"),
        _trait("Shelf Life", "Quality", "days", "days", "Numerical", 7, 300, "Storage observation", "Days until market quality loss."),
        _trait("Total Soluble Solids / Brix", "Quality", "degree Brix", "degree Brix", "Numerical", 3, 25, "Refractometer reading", "Total soluble solids."),
    ),
    "Plantation & Industrial Crops": (
        _trait("Primary Product Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 100, 20000, "Primary product harvest", "Yield of the main harvested product."),
        _trait("Days to First Harvest", "Phenological", "days", "days", "Numerical", 60, 2500, "First harvest timing", "Days from planting to first harvest."),
        _score_trait("Quality Score", "Quality"),
        _score_trait("Pest Resistance", "Biotic Stress"),
        _score_trait("Disease Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _score_trait("Plant Vigor", "Morphological"),
        _trait("Fiber Length", "Quality", "mm", "mm", "Numerical", 5, 3500, "Fiber length assay", "Fiber length."),
        _trait("Oil Content", "Quality", "%", "%", "Numerical", 5, 75, "Oil assay", "Oil content percentage."),
        _trait("Caffeine Content", "Quality", "%", "%", "Numerical", 0, 6, "Caffeine assay", "Caffeine content percentage."),
    ),
    "Spices & Herbs": (
        _trait("Fresh Herb Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 0.5, 80, "Fresh harvest", "Fresh herb or spice biomass yield."),
        _trait("Dry Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 0.1, 25, "Dry harvest", "Dried product yield."),
        _trait("Essential Oil Content", "Quality", "%", "%", "Numerical", 0.1, 10, "Oil distillation assay", "Essential oil percentage."),
        _trait("Days to First Harvest", "Phenological", "days", "days", "Numerical", 25, 360, "First harvest timing", "Days from planting to first harvest."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 5, 300, "Plant height measurement", "Ground-to-apex plant height."),
        _trait("Leaf Area Index", "Morphological", "index", None, "Numerical", 0.1, 12, "Canopy measurement", "Leaf area index."),
        _score_trait("Aroma Intensity", "Quality"),
        _score_trait("Powdery Mildew Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _trait("Active Compound Content", "Quality", "%", "%", "Numerical", 0.01, 20, "Compound assay", "Active compound percentage."),
    ),
    "Nuts": (
        _trait("Nut Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 100, 12000, "Nut harvest", "Marketable nut yield."),
        _trait("Average Nut Weight", "Yield Component", "g", "g", "Numerical", 0.1, 50, "Nut weighing", "Mean nut weight."),
        _trait("Kernel Recovery", "Quality", "%", "%", "Numerical", 10, 90, "Shelling recovery", "Kernel percentage after shelling."),
        _trait("Oil Content", "Quality", "%", "%", "Numerical", 20, 80, "Oil assay", "Kernel oil percentage."),
        _trait("Protein Content", "Quality", "%", "%", "Numerical", 5, 35, "Protein assay", "Kernel protein percentage."),
        _trait("Days to Harvest", "Phenological", "days", "days", "Numerical", 90, 320, "Harvest timing", "Days from bloom or season start to harvest."),
        _trait("Shell Thickness", "Quality", "mm", "mm", "Numerical", 0.1, 8, "Shell measurement", "Shell thickness."),
        _score_trait("Aflatoxin Susceptibility", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _trait("Alternate Bearing Index", "Phenological", "index", None, "Numerical", 0, 1, "Bearing stability index", "Year-to-year bearing variability index."),
    ),
    "Fodder & Forage Crops": (
        _trait("Fresh Biomass Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 2, 180, "Fresh biomass harvest", "Fresh forage biomass yield."),
        _trait("Dry Matter Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 0.5, 45, "Dry matter harvest", "Dry matter forage yield."),
        _trait("Crude Protein Content", "Quality", "%", "%", "Numerical", 3, 35, "Crude protein assay", "Forage crude protein percentage."),
        _trait("Neutral Detergent Fiber", "Quality", "%", "%", "Numerical", 20, 85, "NDF assay", "Neutral detergent fiber."),
        _trait("Acid Detergent Fiber", "Quality", "%", "%", "Numerical", 10, 70, "ADF assay", "Acid detergent fiber."),
        _trait("Number of Cuts per Year", "Agronomic", "count", "count", "Numerical", 1, 12, "Cut count", "Harvest cuts per year."),
        _trait("Days to First Cut", "Phenological", "days", "days", "Numerical", 20, 180, "First cut timing", "Days from sowing to first cut."),
        _score_trait("Regrowth Vigor", "Agronomic"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _score_trait("Stem Borer Resistance", "Biotic Stress"),
    ),
    "Fiber Crops": (
        _trait("Fiber Yield", "Agronomic", "kg/ha", "kg/ha", "Numerical", 100, 10000, "Fiber harvest", "Fiber yield."),
        _trait("Fiber Length", "Quality", "mm", "mm", "Numerical", 5, 3500, "Fiber length assay", "Fiber length."),
        _trait("Fiber Strength", "Quality", "g/tex", "g/tex", "Numerical", 5, 80, "Fiber strength assay", "Fiber strength."),
        _trait("Fiber Fineness / Micronaire", "Quality", "micronaire", "micronaire", "Numerical", 2, 8, "Micronaire assay", "Fiber fineness."),
        _trait("Uniformity Index", "Quality", "%", "%", "Numerical", 50, 100, "Fiber uniformity assay", "Fiber uniformity percentage."),
        _trait("Days to Maturity", "Phenological", "days", "days", "Numerical", 80, 240, "Days to maturity", "Days from sowing to maturity."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 30, 500, "Plant height measurement", "Ground-to-apex plant height."),
        _trait("Boll Weight", "Yield Component", "g", "g", "Numerical", 1, 12, "Boll weighing", "Mean boll weight."),
        _score_trait("Bollworm Resistance", "Biotic Stress"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
    ),
    "Medicinal & Aromatic Plants": (
        _trait("Fresh Biomass Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 0.5, 100, "Fresh biomass harvest", "Fresh biomass yield."),
        _trait("Dry Herb Yield", "Agronomic", "t/ha", "t/ha", "Numerical", 0.1, 30, "Dry herb harvest", "Dry herb yield."),
        _trait("Essential Oil Yield", "Quality", "kg/ha", "kg/ha", "Numerical", 1, 600, "Oil yield calculation", "Essential oil yield per hectare."),
        _trait("Active Compound Content", "Quality", "%", "%", "Numerical", 0.01, 25, "Compound assay", "Active compound percentage."),
        _trait("Days to First Harvest", "Phenological", "days", "days", "Numerical", 30, 540, "First harvest timing", "Days from planting to first harvest."),
        _trait("Plant Height", "Morphological", "cm", "cm", "Numerical", 5, 400, "Plant height measurement", "Ground-to-apex plant height."),
        _score_trait("Aroma Quality Score", "Quality"),
        _score_trait("Drought Tolerance Score", "Abiotic Stress"),
        _score_trait("Pest Resistance", "Biotic Stress"),
        _score_trait("Regrowth Vigor after Harvest", "Agronomic"),
    ),
}


CATEGORY_TRAIT_REGISTRY["Fruits — Tropical & Subtropical"] = CATEGORY_TRAIT_REGISTRY["Fruits - Tropical & Subtropical"]
CATEGORY_TRAIT_REGISTRY["Fruits — Temperate"] = CATEGORY_TRAIT_REGISTRY["Fruits - Temperate"]
CATEGORY_TRAIT_REGISTRY["Vegetables — Leafy"] = CATEGORY_TRAIT_REGISTRY["Vegetables - Leafy"]
CATEGORY_TRAIT_REGISTRY["Vegetables — Fruiting"] = CATEGORY_TRAIT_REGISTRY["Vegetables - Fruiting"]
CATEGORY_TRAIT_REGISTRY["Vegetables — Bulb & Root"] = CATEGORY_TRAIT_REGISTRY["Vegetables - Bulb & Root"]


def get_traits_for_crop(category: str) -> list[TraitDef]:
    return list(CATEGORY_TRAIT_REGISTRY.get(category) or CATEGORY_TRAIT_REGISTRY["Cereals & Grains"])
