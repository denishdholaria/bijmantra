"""
Additional DUS Crop Templates

UPOV-compliant character definitions for:
- Cotton (Gossypium hirsutum)
- Castor (Ricinus communis)
- Groundnut/Peanut (Arachis hypogaea)
- Cumin (Cuminum cyminum)
- Pigeonpea (Cajanus cajan)
- Soybean (Glycine max)
- Chickpea (Cicer arietinum)
"""

from app.services.dus_testing import DUSCharacter, CropTemplate, CharacterType


# ============ Cotton (Gossypium hirsutum) - UPOV TG/88/6 ============

COTTON_CHARACTERS = [
    DUSCharacter(id="cotton_1", number=1, name="Hypocotyl: anthocyanin coloration", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="cotton_2", number=2, name="Leaf: shape", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Palmate"}, {"code": 2, "description": "Semi-digitate"}, {"code": 3, "description": "Digitate"}, {"code": 4, "description": "Okra"}, {"code": 5, "description": "Super okra"}]),
    DUSCharacter(id="cotton_3", number=3, name="Leaf: size", type=CharacterType.MG, grouping=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="cotton_4", number=4, name="Leaf: intensity of green color", type=CharacterType.VG,
                 states=[{"code": 3, "description": "Light"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dark"}]),
    DUSCharacter(id="cotton_5", number=5, name="Leaf: nectaries", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="cotton_6", number=6, name="Leaf: pubescence of lower side", type=CharacterType.VG,
                 states=[{"code": 1, "description": "Absent or very sparse"}, {"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="cotton_7", number=7, name="Stem: pubescence", type=CharacterType.VG,
                 states=[{"code": 1, "description": "Absent or very sparse"}, {"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="cotton_8", number=8, name="Stem: anthocyanin coloration", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="cotton_9", number=9, name="Petal: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Cream"}, {"code": 3, "description": "Yellow"}, {"code": 4, "description": "Pink"}, {"code": 5, "description": "Red"}]),
    DUSCharacter(id="cotton_10", number=10, name="Petal: spot", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="cotton_11", number=11, name="Pollen: color", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Cream"}, {"code": 3, "description": "Yellow"}]),
    DUSCharacter(id="cotton_12", number=12, name="Boll: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Round"}, {"code": 2, "description": "Ovate"}, {"code": 3, "description": "Elliptic"}, {"code": 4, "description": "Oblong"}]),
    DUSCharacter(id="cotton_13", number=13, name="Boll: size", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="cotton_14", number=14, name="Boll: surface", type=CharacterType.VG,
                 states=[{"code": 1, "description": "Smooth"}, {"code": 2, "description": "Pitted"}]),
    DUSCharacter(id="cotton_15", number=15, name="Boll: number of locules", type=CharacterType.QN, grouping=True,
                 states=[{"code": 3, "description": "Three"}, {"code": 4, "description": "Four"}, {"code": 5, "description": "Five"}]),
    DUSCharacter(id="cotton_16", number=16, name="Fiber: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Cream"}, {"code": 3, "description": "Light brown"}, {"code": 4, "description": "Brown"}, {"code": 5, "description": "Green"}]),
    DUSCharacter(id="cotton_17", number=17, name="Seed: fuzz", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent (naked)"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="cotton_18", number=18, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

COTTON_TEMPLATE = CropTemplate(
    crop_code="cotton",
    crop_name="Cotton",
    scientific_name="Gossypium hirsutum L.",
    upov_code="GOSSY_HIR",
    test_guideline="TG/88/6",
    characters=COTTON_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)



# ============ Castor (Ricinus communis) - UPOV TG/278/1 ============

CASTOR_CHARACTERS = [
    DUSCharacter(id="castor_1", number=1, name="Seedling: anthocyanin coloration of hypocotyl", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="castor_2", number=2, name="Stem: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Green"}, {"code": 2, "description": "Green with red"}, {"code": 3, "description": "Red"}, {"code": 4, "description": "Purple"}]),
    DUSCharacter(id="castor_3", number=3, name="Stem: wax coating (bloom)", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="castor_4", number=4, name="Leaf: shape", type=CharacterType.PQ, grouping=True,
                 states=[{"code": 1, "description": "Palmate with shallow lobes"}, {"code": 2, "description": "Palmate with medium lobes"}, {"code": 3, "description": "Palmate with deep lobes"}]),
    DUSCharacter(id="castor_5", number=5, name="Leaf: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Green"}, {"code": 2, "description": "Green with red veins"}, {"code": 3, "description": "Red"}, {"code": 4, "description": "Purple"}]),
    DUSCharacter(id="castor_6", number=6, name="Leaf: wax coating", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent or very weak"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="castor_7", number=7, name="Leaf: size", type=CharacterType.MG, grouping=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="castor_8", number=8, name="Inflorescence: type", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Monoecious"}, {"code": 2, "description": "Interspersed"}, {"code": 3, "description": "Pistillate"}]),
    DUSCharacter(id="castor_9", number=9, name="Capsule: spines", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="castor_10", number=10, name="Capsule: color at maturity", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "Green"}, {"code": 2, "description": "Red"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="castor_11", number=11, name="Capsule: dehiscence", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Dehiscent"}, {"code": 2, "description": "Semi-dehiscent"}, {"code": 3, "description": "Indehiscent"}]),
    DUSCharacter(id="castor_12", number=12, name="Seed: size", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="castor_13", number=13, name="Seed: ground color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Grey"}, {"code": 3, "description": "Brown"}, {"code": 4, "description": "Red brown"}]),
    DUSCharacter(id="castor_14", number=14, name="Seed: mottling", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="castor_15", number=15, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

CASTOR_TEMPLATE = CropTemplate(
    crop_code="castor",
    crop_name="Castor",
    scientific_name="Ricinus communis L.",
    upov_code="RICIN_COM",
    test_guideline="TG/278/1",
    characters=CASTOR_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# ============ Groundnut/Peanut (Arachis hypogaea) - UPOV TG/93/4 ============

GROUNDNUT_CHARACTERS = [
    DUSCharacter(id="groundnut_1", number=1, name="Plant: growth habit", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Bunch (erect)"}, {"code": 2, "description": "Semi-spreading"}, {"code": 3, "description": "Spreading (runner)"}]),
    DUSCharacter(id="groundnut_2", number=2, name="Plant: branching pattern", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Sequential"}, {"code": 2, "description": "Alternate"}]),
    DUSCharacter(id="groundnut_3", number=3, name="Stem: anthocyanin coloration", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="groundnut_4", number=4, name="Stem: pubescence", type=CharacterType.VG,
                 states=[{"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="groundnut_5", number=5, name="Leaf: color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Light green"}, {"code": 5, "description": "Medium green"}, {"code": 7, "description": "Dark green"}]),
    DUSCharacter(id="groundnut_6", number=6, name="Leaflet: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Oblong"}, {"code": 2, "description": "Elliptic"}, {"code": 3, "description": "Obovate"}]),
    DUSCharacter(id="groundnut_7", number=7, name="Leaflet: size", type=CharacterType.MG, grouping=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="groundnut_8", number=8, name="Flower: standard petal color", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "Yellow"}, {"code": 2, "description": "Orange yellow"}, {"code": 3, "description": "Orange"}]),
    DUSCharacter(id="groundnut_9", number=9, name="Pod: beak", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Slight"}, {"code": 5, "description": "Moderate"}, {"code": 7, "description": "Prominent"}]),
    DUSCharacter(id="groundnut_10", number=10, name="Pod: constriction", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "None"}, {"code": 3, "description": "Slight"}, {"code": 5, "description": "Moderate"}, {"code": 7, "description": "Deep"}]),
    DUSCharacter(id="groundnut_11", number=11, name="Pod: reticulation", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 3, "description": "Slight"}, {"code": 5, "description": "Moderate"}, {"code": 7, "description": "Prominent"}]),
    DUSCharacter(id="groundnut_12", number=12, name="Pod: number of seeds", type=CharacterType.QN, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "One"}, {"code": 2, "description": "Two"}, {"code": 3, "description": "Three"}, {"code": 4, "description": "Four or more"}]),
    DUSCharacter(id="groundnut_13", number=13, name="Seed: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Round"}, {"code": 2, "description": "Oval"}, {"code": 3, "description": "Oblong"}]),
    DUSCharacter(id="groundnut_14", number=14, name="Seed: size", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="groundnut_15", number=15, name="Seed: testa color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Rose"}, {"code": 3, "description": "Red"}, {"code": 4, "description": "Purple"}, {"code": 5, "description": "Tan"}]),
    DUSCharacter(id="groundnut_16", number=16, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
    DUSCharacter(id="groundnut_17", number=17, name="Time of maturity", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

GROUNDNUT_TEMPLATE = CropTemplate(
    crop_code="groundnut",
    crop_name="Groundnut (Peanut)",
    scientific_name="Arachis hypogaea L.",
    upov_code="ARACH_HYP",
    test_guideline="TG/93/4",
    characters=GROUNDNUT_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)



# ============ Cumin (Cuminum cyminum) - India PPV&FRA Guidelines ============

CUMIN_CHARACTERS = [
    DUSCharacter(id="cumin_1", number=1, name="Plant: growth habit", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Spreading"}]),
    DUSCharacter(id="cumin_2", number=2, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}]),
    DUSCharacter(id="cumin_3", number=3, name="Stem: anthocyanin coloration", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="cumin_4", number=4, name="Stem: branching", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Few"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Many"}]),
    DUSCharacter(id="cumin_5", number=5, name="Leaf: color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Light green"}, {"code": 5, "description": "Medium green"}, {"code": 7, "description": "Dark green"}]),
    DUSCharacter(id="cumin_6", number=6, name="Leaf: division", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 3, "description": "Coarse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Fine"}]),
    DUSCharacter(id="cumin_7", number=7, name="Flower: color", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Pink"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="cumin_8", number=8, name="Umbel: number of rays", type=CharacterType.QN, grouping=True,
                 states=[{"code": 3, "description": "Few (3-5)"}, {"code": 5, "description": "Medium (6-8)"}, {"code": 7, "description": "Many (>8)"}]),
    DUSCharacter(id="cumin_9", number=9, name="Seed: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Oblong"}, {"code": 2, "description": "Elliptic"}, {"code": 3, "description": "Fusiform"}]),
    DUSCharacter(id="cumin_10", number=10, name="Seed: size", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="cumin_11", number=11, name="Seed: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Light brown"}, {"code": 2, "description": "Brown"}, {"code": 3, "description": "Dark brown"}, {"code": 4, "description": "Greenish brown"}]),
    DUSCharacter(id="cumin_12", number=12, name="Seed: ridges prominence", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 3, "description": "Slight"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Prominent"}]),
    DUSCharacter(id="cumin_13", number=13, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
    DUSCharacter(id="cumin_14", number=14, name="Time of maturity", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

CUMIN_TEMPLATE = CropTemplate(
    crop_code="cumin",
    crop_name="Cumin",
    scientific_name="Cuminum cyminum L.",
    upov_code="CUMIN_CYM",
    test_guideline="PPV&FRA/TG/CUMIN",
    characters=CUMIN_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# ============ Pigeonpea (Cajanus cajan) - UPOV TG/XXX (India PPV&FRA) ============

PIGEONPEA_CHARACTERS = [
    DUSCharacter(id="pigeonpea_1", number=1, name="Plant: growth habit", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Determinate"}, {"code": 2, "description": "Semi-determinate"}, {"code": 3, "description": "Indeterminate"}]),
    DUSCharacter(id="pigeonpea_2", number=2, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Short (<100 cm)"}, {"code": 5, "description": "Medium (100-175 cm)"}, {"code": 7, "description": "Tall (>175 cm)"}]),
    DUSCharacter(id="pigeonpea_3", number=3, name="Stem: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Green"}, {"code": 2, "description": "Green with purple streaks"}, {"code": 3, "description": "Purple"}]),
    DUSCharacter(id="pigeonpea_4", number=4, name="Stem: pubescence", type=CharacterType.VG,
                 states=[{"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="pigeonpea_5", number=5, name="Leaf: color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Light green"}, {"code": 5, "description": "Medium green"}, {"code": 7, "description": "Dark green"}]),
    DUSCharacter(id="pigeonpea_6", number=6, name="Leaflet: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Lanceolate"}, {"code": 2, "description": "Elliptic"}, {"code": 3, "description": "Obovate"}]),
    DUSCharacter(id="pigeonpea_7", number=7, name="Flower: standard petal color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Yellow"}, {"code": 2, "description": "Yellow with red streaks"}, {"code": 3, "description": "Red"}]),
    DUSCharacter(id="pigeonpea_8", number=8, name="Flower: streak pattern on standard", type=CharacterType.PQ, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 2, "description": "Few streaks"}, {"code": 3, "description": "Dense streaks"}]),
    DUSCharacter(id="pigeonpea_9", number=9, name="Pod: color at maturity", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Green"}, {"code": 2, "description": "Green with purple"}, {"code": 3, "description": "Purple"}, {"code": 4, "description": "Dark purple"}]),
    DUSCharacter(id="pigeonpea_10", number=10, name="Pod: number of seeds", type=CharacterType.QN, grouping=True,
                 states=[{"code": 3, "description": "Few (2-3)"}, {"code": 5, "description": "Medium (4-5)"}, {"code": 7, "description": "Many (>5)"}]),
    DUSCharacter(id="pigeonpea_11", number=11, name="Seed: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Round"}, {"code": 2, "description": "Oval"}, {"code": 3, "description": "Pea-shaped"}]),
    DUSCharacter(id="pigeonpea_12", number=12, name="Seed: size (100 seed weight)", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small (<8g)"}, {"code": 5, "description": "Medium (8-12g)"}, {"code": 7, "description": "Large (>12g)"}]),
    DUSCharacter(id="pigeonpea_13", number=13, name="Seed: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Cream"}, {"code": 3, "description": "Grey"}, {"code": 4, "description": "Brown"}, {"code": 5, "description": "Purple"}]),
    DUSCharacter(id="pigeonpea_14", number=14, name="Seed: mottling", type=CharacterType.QL, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="pigeonpea_15", number=15, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early (<100 days)"}, {"code": 5, "description": "Medium (100-140 days)"}, {"code": 7, "description": "Late (>140 days)"}]),
    DUSCharacter(id="pigeonpea_16", number=16, name="Time of maturity", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early (<130 days)"}, {"code": 5, "description": "Medium (130-180 days)"}, {"code": 7, "description": "Late (>180 days)"}]),
]

PIGEONPEA_TEMPLATE = CropTemplate(
    crop_code="pigeonpea",
    crop_name="Pigeonpea (Red Gram)",
    scientific_name="Cajanus cajan (L.) Millsp.",
    upov_code="CAJAN_CAJ",
    test_guideline="PPV&FRA/TG/PIGEONPEA",
    characters=PIGEONPEA_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)



# ============ Soybean (Glycine max) - UPOV TG/80/7 ============

SOYBEAN_CHARACTERS = [
    DUSCharacter(id="soybean_1", number=1, name="Plant: growth type", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Determinate"}, {"code": 2, "description": "Semi-determinate"}, {"code": 3, "description": "Indeterminate"}]),
    DUSCharacter(id="soybean_2", number=2, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}]),
    DUSCharacter(id="soybean_3", number=3, name="Hypocotyl: anthocyanin coloration", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 9, "description": "Present"}]),
    DUSCharacter(id="soybean_4", number=4, name="Leaf: shape of lateral leaflet", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Narrow"}, {"code": 2, "description": "Intermediate"}, {"code": 3, "description": "Broad"}]),
    DUSCharacter(id="soybean_5", number=5, name="Leaf: intensity of green color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Light"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dark"}]),
    DUSCharacter(id="soybean_6", number=6, name="Leaf: pubescence", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="soybean_7", number=7, name="Flower: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Purple"}]),
    DUSCharacter(id="soybean_8", number=8, name="Pod: color of pubescence", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Grey"}, {"code": 2, "description": "Tawny (brown)"}]),
    DUSCharacter(id="soybean_9", number=9, name="Pod: number of seeds", type=CharacterType.QN, grouping=True,
                 states=[{"code": 1, "description": "One"}, {"code": 2, "description": "Two"}, {"code": 3, "description": "Three"}, {"code": 4, "description": "Four"}]),
    DUSCharacter(id="soybean_10", number=10, name="Seed: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Spherical"}, {"code": 2, "description": "Spherical flattened"}, {"code": 3, "description": "Elongated"}, {"code": 4, "description": "Elongated flattened"}]),
    DUSCharacter(id="soybean_11", number=11, name="Seed: size (100 seed weight)", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small (<10g)"}, {"code": 5, "description": "Medium (10-20g)"}, {"code": 7, "description": "Large (>20g)"}]),
    DUSCharacter(id="soybean_12", number=12, name="Seed: testa color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Yellow"}, {"code": 2, "description": "Yellow-green"}, {"code": 3, "description": "Green"}, {"code": 4, "description": "Brown"}, {"code": 5, "description": "Black"}]),
    DUSCharacter(id="soybean_13", number=13, name="Seed: hilum color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Yellow"}, {"code": 2, "description": "Light brown"}, {"code": 3, "description": "Brown"}, {"code": 4, "description": "Black"}, {"code": 5, "description": "Imperfect black"}]),
    DUSCharacter(id="soybean_14", number=14, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
    DUSCharacter(id="soybean_15", number=15, name="Time of maturity", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

SOYBEAN_TEMPLATE = CropTemplate(
    crop_code="soybean",
    crop_name="Soybean",
    scientific_name="Glycine max (L.) Merr.",
    upov_code="GLYCI_MAX",
    test_guideline="TG/80/7",
    characters=SOYBEAN_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# ============ Chickpea (Cicer arietinum) - UPOV TG/143/5 ============
# Note: Chickpea is the correct scientific name. Bengal gram is a common name in India.

CHICKPEA_CHARACTERS = [
    DUSCharacter(id="chickpea_1", number=1, name="Plant: growth habit", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Erect"}, {"code": 3, "description": "Semi-erect"}, {"code": 5, "description": "Semi-spreading"}, {"code": 7, "description": "Spreading"}, {"code": 9, "description": "Prostrate"}]),
    DUSCharacter(id="chickpea_2", number=2, name="Plant: height", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Short"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Tall"}]),
    DUSCharacter(id="chickpea_3", number=3, name="Stem: anthocyanin coloration", type=CharacterType.VG, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Absent"}, {"code": 3, "description": "Weak"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Strong"}]),
    DUSCharacter(id="chickpea_4", number=4, name="Stem: pubescence", type=CharacterType.VG,
                 states=[{"code": 3, "description": "Sparse"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Dense"}]),
    DUSCharacter(id="chickpea_5", number=5, name="Leaf: type", type=CharacterType.QL, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Simple"}, {"code": 2, "description": "Fern-like (normal)"}]),
    DUSCharacter(id="chickpea_6", number=6, name="Leaf: color", type=CharacterType.VG, grouping=True,
                 states=[{"code": 3, "description": "Light green"}, {"code": 5, "description": "Medium green"}, {"code": 7, "description": "Dark green"}]),
    DUSCharacter(id="chickpea_7", number=7, name="Leaflet: size", type=CharacterType.MG, grouping=True,
                 states=[{"code": 3, "description": "Small"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Large"}]),
    DUSCharacter(id="chickpea_8", number=8, name="Flower: color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "White"}, {"code": 2, "description": "Pink"}, {"code": 3, "description": "Blue"}, {"code": 4, "description": "Purple"}]),
    DUSCharacter(id="chickpea_9", number=9, name="Pod: number of seeds", type=CharacterType.QN, grouping=True,
                 states=[{"code": 1, "description": "One"}, {"code": 2, "description": "Two"}, {"code": 3, "description": "Three"}]),
    DUSCharacter(id="chickpea_10", number=10, name="Seed: type", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Desi (angular)"}, {"code": 2, "description": "Kabuli (owl's head)"}, {"code": 3, "description": "Intermediate"}]),
    DUSCharacter(id="chickpea_11", number=11, name="Seed: shape", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Angular"}, {"code": 2, "description": "Owl's head"}, {"code": 3, "description": "Pea-shaped"}, {"code": 4, "description": "Irregular"}]),
    DUSCharacter(id="chickpea_12", number=12, name="Seed: size (100 seed weight)", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Small (<15g)"}, {"code": 5, "description": "Medium (15-25g)"}, {"code": 7, "description": "Large (>25g)"}]),
    DUSCharacter(id="chickpea_13", number=13, name="Seed: testa color", type=CharacterType.PQ, grouping=True, asterisk=True,
                 states=[{"code": 1, "description": "Cream/Beige"}, {"code": 2, "description": "Yellow"}, {"code": 3, "description": "Orange"}, {"code": 4, "description": "Brown"}, {"code": 5, "description": "Black"}]),
    DUSCharacter(id="chickpea_14", number=14, name="Seed: testa texture", type=CharacterType.VG, asterisk=True,
                 states=[{"code": 1, "description": "Smooth"}, {"code": 2, "description": "Rough"}, {"code": 3, "description": "Tuberculated"}]),
    DUSCharacter(id="chickpea_15", number=15, name="Time of flowering", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
    DUSCharacter(id="chickpea_16", number=16, name="Time of maturity", type=CharacterType.MG, grouping=True, asterisk=True,
                 states=[{"code": 3, "description": "Early"}, {"code": 5, "description": "Medium"}, {"code": 7, "description": "Late"}]),
]

CHICKPEA_TEMPLATE = CropTemplate(
    crop_code="chickpea",
    crop_name="Chickpea (Bengal Gram)",
    scientific_name="Cicer arietinum L.",
    upov_code="CICER_ARI",
    test_guideline="TG/143/5",
    characters=CHICKPEA_CHARACTERS,
    uniformity_threshold=1.0,
    min_sample_size=100,
    test_years=2,
)


# ============ Export all templates ============

ADDITIONAL_CROP_TEMPLATES = {
    "cotton": COTTON_TEMPLATE,
    "castor": CASTOR_TEMPLATE,
    "groundnut": GROUNDNUT_TEMPLATE,
    "cumin": CUMIN_TEMPLATE,
    "pigeonpea": PIGEONPEA_TEMPLATE,
    "soybean": SOYBEAN_TEMPLATE,
    "chickpea": CHICKPEA_TEMPLATE,
}
