"""Demo benchmark alignment seeder.

Seeds deterministic linked observations and a benchmark-aligned wheat trial inside the
Demo Organization so REEVU can exercise authoritative breeding and trial paths locally.
"""

import logging

from sqlalchemy import select

from app.core.demo_dataset import DEMO_DATASET_ORG_NAME, demo_dataset_datetime, stable_demo_id
from app.db.seeders.base import BaseSeeder, register_seeder


logger = logging.getLogger(__name__)


BENCHMARK_GERMPLASM_TRAITS = {
    "IR64": ["Blast Resistance", "Grain Yield"],
    "Swarna": ["Blast Resistance", "Grain Yield"],
    "HD2967": ["Drought Tolerance", "Grain Yield"],
    "PBW343": ["Drought Tolerance", "Grain Yield"],
    "Kalyan Sona": ["Drought Tolerance", "Grain Yield"],
}

BENCHMARK_TRIAL_NAME = "Ludhiana Advanced Yield Trial 2025"
BENCHMARK_STUDY_NAME = "LAYT-2025-PAU"

BENCHMARK_VARIABLES = [
    {
        "observation_variable_name": "Drought Tolerance Score",
        "common_crop_name": "Wheat",
        "trait_name": "Drought Tolerance",
        "trait_description": "Visual drought-tolerance score under managed stress.",
        "trait_class": "Abiotic Stress",
        "method_name": "Visual Scoring",
        "method_description": "Score on a 1-9 scale where lower scores indicate better tolerance.",
        "scale_name": "1-9 scale",
        "data_type": "Ordinal",
        "valid_values": {"categories": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
        "status": "active",
    }
]

BENCHMARK_PROTOCOLS = [
    {
        "name": "Rice Blast Resistance Speed Breeding Protocol",
        "description": (
            "Accelerated rice generation advancement protocol for blast-resistance improvement "
            "under controlled long-day conditions."
        ),
        "crop": "Rice",
        "photoperiod": 22,
        "temperature_day": 30.0,
        "temperature_night": 26.0,
        "humidity": 70.0,
        "light_intensity": 450.0,
        "days_to_flower": 38,
        "days_to_harvest": 82,
        "generations_per_year": 4.2,
        "success_rate": 0.91,
        "status": "active",
    }
]

BENCHMARK_UNITS = [
    {
        "unit_name": "RYT-IR64-REP1",
        "study_name": "RYT-2024-LOC1",
        "germplasm_name": "IR64",
        "entry_type": "check",
        "x": "1",
        "y": "A",
        "observations": {
            "Grain Yield": "6120",
            "Disease Score": "3",
        },
    },
    {
        "unit_name": "RYT-IR64-REP2",
        "study_name": "RYT-2024-LOC1",
        "germplasm_name": "IR64",
        "entry_type": "check",
        "x": "1",
        "y": "B",
        "observations": {
            "Grain Yield": "6055",
            "Disease Score": "2",
        },
    },
    {
        "unit_name": "RYT-Swarna-REP1",
        "study_name": "RYT-2024-LOC1",
        "germplasm_name": "Swarna",
        "entry_type": "test",
        "x": "2",
        "y": "A",
        "observations": {
            "Grain Yield": "5780",
            "Disease Score": "5",
        },
    },
    {
        "unit_name": "RYT-Swarna-REP2",
        "study_name": "RYT-2024-LOC1",
        "germplasm_name": "Swarna",
        "entry_type": "test",
        "x": "2",
        "y": "B",
        "observations": {
            "Grain Yield": "5715",
            "Disease Score": "4",
        },
    },
    {
        "unit_name": "LAYT-HD2967-REP1",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "HD2967",
        "entry_type": "check",
        "x": "1",
        "y": "A",
        "observations": {
            "Grain Yield": "5840",
            "Thousand Grain Weight": "45.2",
            "Drought Tolerance Score": "3",
        },
    },
    {
        "unit_name": "LAYT-HD2967-REP2",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "HD2967",
        "entry_type": "check",
        "x": "1",
        "y": "B",
        "observations": {
            "Grain Yield": "5895",
            "Thousand Grain Weight": "45.8",
            "Drought Tolerance Score": "3",
        },
    },
    {
        "unit_name": "LAYT-PBW343-REP1",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "PBW343",
        "entry_type": "test",
        "x": "2",
        "y": "A",
        "observations": {
            "Grain Yield": "5485",
            "Thousand Grain Weight": "42.1",
            "Drought Tolerance Score": "6",
        },
    },
    {
        "unit_name": "LAYT-PBW343-REP2",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "PBW343",
        "entry_type": "test",
        "x": "2",
        "y": "B",
        "observations": {
            "Grain Yield": "5525",
            "Thousand Grain Weight": "42.4",
            "Drought Tolerance Score": "6",
        },
    },
    {
        "unit_name": "LAYT-KALYAN-REP1",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "Kalyan Sona",
        "entry_type": "test",
        "x": "3",
        "y": "A",
        "observations": {
            "Grain Yield": "5630",
            "Thousand Grain Weight": "43.7",
            "Drought Tolerance Score": "4",
        },
    },
    {
        "unit_name": "LAYT-KALYAN-REP2",
        "study_name": BENCHMARK_STUDY_NAME,
        "germplasm_name": "Kalyan Sona",
        "entry_type": "test",
        "x": "3",
        "y": "B",
        "observations": {
            "Grain Yield": "5595",
            "Thousand Grain Weight": "43.2",
            "Drought Tolerance Score": "4",
        },
    },
]

BENCHMARK_WHEAT_VARIANT_SET_NAME = "Wheat Training Population SNP Panel"

BENCHMARK_WHEAT_VARIANTS = [
    {"name": "WHT_SNP_1A_01050", "chromosome": "1A", "start": 1050, "ref": "A", "alt": "G"},
    {"name": "WHT_SNP_1B_08420", "chromosome": "1B", "start": 8420, "ref": "C", "alt": "T"},
    {"name": "WHT_SNP_2A_12610", "chromosome": "2A", "start": 12610, "ref": "G", "alt": "A"},
    {"name": "WHT_SNP_3B_21105", "chromosome": "3B", "start": 21105, "ref": "T", "alt": "C"},
    {"name": "WHT_SNP_5D_30990", "chromosome": "5D", "start": 30990, "ref": "A", "alt": "C"},
]

BENCHMARK_WHEAT_TRAINING_POPULATION = [
    {
        "germplasm_name": "HD2967",
        "unit_name": "LAYT-HD2967-REP1",
        "sample_name": "LAYT-HD2967-DNA",
        "genotypes": ["0/0", "0/1", "1/1", "0/0", "0/1"],
    },
    {
        "germplasm_name": "PBW343",
        "unit_name": "LAYT-PBW343-REP1",
        "sample_name": "LAYT-PBW343-DNA",
        "genotypes": ["0/1", "0/1", "0/0", "1/1", "0/0"],
    },
    {
        "germplasm_name": "Kalyan Sona",
        "unit_name": "LAYT-KALYAN-REP1",
        "sample_name": "LAYT-KALYAN-DNA",
        "genotypes": ["1/1", "0/0", "0/1", "0/0", "1/1"],
    },
]


def _merge_traits(existing_traits: list[str], new_traits: list[str]) -> list[str]:
    return sorted({trait for trait in [*existing_traits, *new_traits] if trait})


@register_seeder
class DemoBenchmarkAlignmentSeeder(BaseSeeder):
    """Seeds benchmark-aligned linked trial and observation data for Demo Organization."""

    name = "demo_benchmark_alignment"
    description = "Benchmark-aligned Demo Org trials and linked observations for REEVU"

    def seed(self) -> int:
        from app.models.core import Location, Organization, Program, Study, Trial
        from app.models.germplasm import Germplasm
        from app.models.genotyping import Call, CallSet, Variant, VariantSet
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable, Sample
        from app.models.speed_breeding import SpeedBreedingProtocol

        demo_org = self.db.execute(
            select(Organization).where(Organization.name == DEMO_DATASET_ORG_NAME)
        ).scalar_one_or_none()
        if not demo_org:
            logger.warning("Demo Organization not found. Run the core demo seeders first.")
            return 0

        org_id = demo_org.id
        seeded = 0
        timestamp = demo_dataset_datetime().isoformat().replace("+00:00", "Z")

        germplasm_by_name = {
            germplasm.germplasm_name: germplasm
            for germplasm in self.db.query(Germplasm).filter(Germplasm.organization_id == org_id).all()
        }
        for germplasm_name, traits in BENCHMARK_GERMPLASM_TRAITS.items():
            germplasm = germplasm_by_name.get(germplasm_name)
            if germplasm is None:
                continue
            additional_info = dict(germplasm.additional_info or {})
            existing_traits = [
                trait for trait in additional_info.get("traits", []) if isinstance(trait, str) and trait.strip()
            ]
            merged_traits = _merge_traits(existing_traits, traits)
            if merged_traits != sorted(existing_traits):
                additional_info["traits"] = merged_traits
                germplasm.additional_info = additional_info
                seeded += 1

        variables_by_name = {
            variable.observation_variable_name: variable
            for variable in self.db.query(ObservationVariable)
            .filter(ObservationVariable.organization_id == org_id)
            .all()
        }
        for variable_data in BENCHMARK_VARIABLES:
            variable = variables_by_name.get(variable_data["observation_variable_name"])
            if variable is None:
                variable = ObservationVariable(
                    organization_id=org_id,
                    observation_variable_db_id=stable_demo_id(
                        "demo_var",
                        variable_data["observation_variable_name"],
                    ),
                    observation_variable_name=variable_data["observation_variable_name"],
                )
                self.db.add(variable)
                seeded += 1

            variable.common_crop_name = variable_data["common_crop_name"]
            variable.trait_name = variable_data["trait_name"]
            variable.trait_description = variable_data["trait_description"]
            variable.trait_class = variable_data["trait_class"]
            variable.method_name = variable_data["method_name"]
            variable.method_description = variable_data["method_description"]
            variable.scale_name = variable_data["scale_name"]
            variable.data_type = variable_data["data_type"]
            variable.valid_values = variable_data["valid_values"]
            variable.status = variable_data["status"]
            variables_by_name[variable.observation_variable_name] = variable

        protocols_by_name = {
            protocol.name: protocol
            for protocol in self.db.query(SpeedBreedingProtocol)
            .filter(SpeedBreedingProtocol.organization_id == org_id)
            .all()
        }
        for protocol_data in BENCHMARK_PROTOCOLS:
            protocol = protocols_by_name.get(protocol_data["name"])
            if protocol is None:
                protocol = SpeedBreedingProtocol(
                    organization_id=org_id,
                    name=protocol_data["name"],
                )
                self.db.add(protocol)
                seeded += 1

            protocol.description = protocol_data["description"]
            protocol.crop = protocol_data["crop"]
            protocol.photoperiod = protocol_data["photoperiod"]
            protocol.temperature_day = protocol_data["temperature_day"]
            protocol.temperature_night = protocol_data["temperature_night"]
            protocol.humidity = protocol_data["humidity"]
            protocol.light_intensity = protocol_data["light_intensity"]
            protocol.days_to_flower = protocol_data["days_to_flower"]
            protocol.days_to_harvest = protocol_data["days_to_harvest"]
            protocol.generations_per_year = protocol_data["generations_per_year"]
            protocol.success_rate = protocol_data["success_rate"]
            protocol.status = protocol_data["status"]

        program = self.db.execute(
            select(Program).where(
                Program.organization_id == org_id,
                Program.program_name == "Wheat Breeding Program",
            )
        ).scalar_one_or_none()
        location = self.db.execute(
            select(Location).where(
                Location.organization_id == org_id,
                Location.location_name == "PAU Research Station",
            )
        ).scalar_one_or_none()
        rice_trial = self.db.execute(
            select(Trial).where(
                Trial.organization_id == org_id,
                Trial.trial_name == "Rice Yield Trial 2024",
            )
        ).scalar_one_or_none()

        if rice_trial is not None and rice_trial.common_crop_name != "Rice":
            rice_trial.common_crop_name = "Rice"

        wheat_study = None
        if program is None or location is None:
            logger.warning(
                "Benchmark alignment skipped the wheat trial because Demo BrAPI program/location seeds are missing."
            )
        else:
            wheat_trial = self.db.execute(
                select(Trial).where(
                    Trial.organization_id == org_id,
                    Trial.trial_name == BENCHMARK_TRIAL_NAME,
                )
            ).scalar_one_or_none()
            if wheat_trial is None:
                wheat_trial = Trial(
                    organization_id=org_id,
                    program_id=program.id,
                    location_id=location.id,
                    trial_db_id=stable_demo_id("demo_trial", BENCHMARK_TRIAL_NAME),
                    trial_name=BENCHMARK_TRIAL_NAME,
                )
                self.db.add(wheat_trial)
                seeded += 1

            wheat_trial.trial_description = (
                "Advanced wheat yield trial at Ludhiana for deterministic REEVU benchmark coverage."
            )
            wheat_trial.trial_type = "Yield Trial"
            wheat_trial.common_crop_name = "Wheat"
            wheat_trial.start_date = "2025-11-15"
            wheat_trial.end_date = "2026-04-15"
            wheat_trial.active = True
            wheat_trial.additional_info = {
                "seeded_for": "reevu-benchmark-alignment",
                "location_context": "Ludhiana",
            }

            self.db.flush()

            wheat_study = self.db.execute(
                select(Study).where(
                    Study.organization_id == org_id,
                    Study.study_name == BENCHMARK_STUDY_NAME,
                )
            ).scalar_one_or_none()
            if wheat_study is None:
                wheat_study = Study(
                    organization_id=org_id,
                    trial_id=wheat_trial.id,
                    location_id=location.id,
                    study_db_id=stable_demo_id("demo_study", BENCHMARK_STUDY_NAME),
                    study_name=BENCHMARK_STUDY_NAME,
                )
                self.db.add(wheat_study)
                seeded += 1

            wheat_study.study_description = "Ludhiana advanced wheat yield trial benchmark study."
            wheat_study.study_type = "Yield Trial"
            wheat_study.common_crop_name = "Wheat"
            wheat_study.start_date = "2025-11-20"
            wheat_study.end_date = "2026-04-10"
            wheat_study.active = True
            wheat_study.observation_units_description = "Benchmark-aligned replicated wheat plots"

        self.db.flush()

        studies_by_name = {
            study.study_name: study
            for study in self.db.query(Study).filter(Study.organization_id == org_id).all()
        }
        units_by_db_id = {
            unit.observation_unit_db_id: unit
            for unit in self.db.query(ObservationUnit)
            .filter(ObservationUnit.organization_id == org_id)
            .all()
        }
        units_by_name = {
            unit.observation_unit_name: unit
            for unit in units_by_db_id.values()
        }
        observations_by_db_id = {
            observation.observation_db_id: observation
            for observation in self.db.query(Observation)
            .filter(Observation.organization_id == org_id)
            .all()
        }

        for unit_data in BENCHMARK_UNITS:
            study = studies_by_name.get(unit_data["study_name"])
            germplasm = germplasm_by_name.get(unit_data["germplasm_name"])
            if study is None or germplasm is None:
                continue

            unit_db_id = stable_demo_id("demo_unit", unit_data["unit_name"])
            unit = units_by_db_id.get(unit_db_id)
            if unit is None:
                unit = ObservationUnit(
                    organization_id=org_id,
                    observation_unit_db_id=unit_db_id,
                    observation_unit_name=unit_data["unit_name"],
                )
                self.db.add(unit)
                units_by_db_id[unit_db_id] = unit
                seeded += 1

            units_by_name[unit_data["unit_name"]] = unit
            unit.study_id = study.id
            unit.germplasm_id = germplasm.id
            unit.observation_level = "plot"
            unit.position_coordinate_x = unit_data["x"]
            unit.position_coordinate_y = unit_data["y"]
            unit.entry_type = unit_data["entry_type"]
            unit.additional_info = {"seeded_for": "reevu-benchmark-alignment"}

            self.db.flush()

            for variable_name, value in unit_data["observations"].items():
                variable = variables_by_name.get(variable_name)
                if variable is None:
                    continue
                observation_db_id = stable_demo_id(
                    "demo_obs",
                    unit_data["unit_name"],
                    variable_name,
                )
                observation = observations_by_db_id.get(observation_db_id)
                if observation is None:
                    observation = Observation(
                        organization_id=org_id,
                        observation_db_id=observation_db_id,
                    )
                    self.db.add(observation)
                    observations_by_db_id[observation_db_id] = observation
                    seeded += 1

                observation.observation_unit_id = unit.id
                observation.observation_variable_id = variable.id
                observation.study_id = study.id
                observation.germplasm_id = germplasm.id
                observation.value = value
                observation.collector = "Demo Benchmark Seeder"
                observation.observation_time_stamp = timestamp
                observation.additional_info = {"seeded_for": "reevu-benchmark-alignment"}

        if wheat_study is not None:
            samples_by_db_id = {
                sample.sample_db_id: sample
                for sample in self.db.query(Sample)
                .filter(Sample.organization_id == org_id)
                .all()
            }
            variant_sets_by_name = {
                variant_set.variant_set_name: variant_set
                for variant_set in self.db.query(VariantSet)
                .filter(VariantSet.organization_id == org_id)
                .all()
            }
            variants_by_db_id = {
                variant.variant_db_id: variant
                for variant in self.db.query(Variant)
                .filter(Variant.organization_id == org_id)
                .all()
            }
            call_sets_by_db_id = {
                call_set.call_set_db_id: call_set
                for call_set in self.db.query(CallSet)
                .filter(CallSet.organization_id == org_id)
                .all()
            }
            calls_by_db_id = {
                call.call_db_id: call
                for call in self.db.query(Call)
                .filter(Call.organization_id == org_id)
                .all()
            }

            variant_set = variant_sets_by_name.get(BENCHMARK_WHEAT_VARIANT_SET_NAME)
            if variant_set is None:
                variant_set = VariantSet(
                    organization_id=org_id,
                    variant_set_db_id=stable_demo_id("demo_variant_set", BENCHMARK_WHEAT_VARIANT_SET_NAME),
                    variant_set_name=BENCHMARK_WHEAT_VARIANT_SET_NAME,
                )
                self.db.add(variant_set)
                variant_sets_by_name[BENCHMARK_WHEAT_VARIANT_SET_NAME] = variant_set
                seeded += 1

            variant_set.study_id = wheat_study.id
            variant_set.call_set_count = len(BENCHMARK_WHEAT_TRAINING_POPULATION)
            variant_set.variant_count = len(BENCHMARK_WHEAT_VARIANTS)
            variant_set.additional_info = {
                "seeded_for": "reevu-benchmark-alignment",
                "crop": "Wheat",
                "population_scope": "training_population",
            }
            self.db.flush()

            for variant_data in BENCHMARK_WHEAT_VARIANTS:
                variant_db_id = stable_demo_id("demo_variant", variant_data["name"])
                variant = variants_by_db_id.get(variant_db_id)
                if variant is None:
                    variant = Variant(
                        organization_id=org_id,
                        variant_set_id=variant_set.id,
                        variant_db_id=variant_db_id,
                        variant_name=variant_data["name"],
                    )
                    self.db.add(variant)
                    variants_by_db_id[variant_db_id] = variant
                    seeded += 1

                variant.variant_set_id = variant_set.id
                variant.variant_type = "SNP"
                variant.reference_bases = variant_data["ref"]
                variant.alternate_bases = [variant_data["alt"]]
                variant.start = variant_data["start"]
                variant.end = variant_data["start"] + 1
                variant.additional_info = {
                    "seeded_for": "reevu-benchmark-alignment",
                    "chromosome": variant_data["chromosome"],
                    "crop": "Wheat",
                }

            self.db.flush()

            for population_entry in BENCHMARK_WHEAT_TRAINING_POPULATION:
                germplasm = germplasm_by_name.get(population_entry["germplasm_name"])
                unit = units_by_name.get(population_entry["unit_name"])
                if germplasm is None or unit is None:
                    continue

                sample_db_id = stable_demo_id("demo_sample", population_entry["sample_name"])
                sample = samples_by_db_id.get(sample_db_id)
                if sample is None:
                    sample = Sample(
                        organization_id=org_id,
                        sample_db_id=sample_db_id,
                        sample_name=population_entry["sample_name"],
                    )
                    self.db.add(sample)
                    samples_by_db_id[sample_db_id] = sample
                    seeded += 1

                sample.observation_unit_id = unit.id
                sample.germplasm_id = germplasm.id
                sample.study_id = wheat_study.id
                sample.sample_type = "DNA"
                sample.tissue_type = "Leaf"
                sample.taken_by = "Demo Benchmark Seeder"
                sample.sample_timestamp = timestamp
                sample.additional_info = {
                    "seeded_for": "reevu-benchmark-alignment",
                    "population_scope": "training_population",
                }
                self.db.flush()

                call_set_db_id = stable_demo_id("demo_call_set", population_entry["germplasm_name"])
                call_set = call_sets_by_db_id.get(call_set_db_id)
                if call_set is None:
                    call_set = CallSet(
                        organization_id=org_id,
                        call_set_db_id=call_set_db_id,
                        call_set_name=population_entry["germplasm_name"],
                    )
                    self.db.add(call_set)
                    call_sets_by_db_id[call_set_db_id] = call_set
                    seeded += 1

                call_set.sample_id = sample.id
                call_set.sample_db_id = sample.sample_db_id
                call_set.created = timestamp
                call_set.updated = timestamp
                call_set.additional_info = {
                    "seeded_for": "reevu-benchmark-alignment",
                    "variant_set_db_id": variant_set.variant_set_db_id,
                }
                self.db.flush()

                for variant_data, genotype_value in zip(
                    BENCHMARK_WHEAT_VARIANTS,
                    population_entry["genotypes"],
                    strict=False,
                ):
                    variant_db_id = stable_demo_id("demo_variant", variant_data["name"])
                    variant = variants_by_db_id[variant_db_id]
                    call_db_id = stable_demo_id(
                        "demo_call",
                        population_entry["germplasm_name"],
                        variant_data["name"],
                    )
                    call = calls_by_db_id.get(call_db_id)
                    if call is None:
                        call = Call(
                            organization_id=org_id,
                            call_db_id=call_db_id,
                            variant_id=variant.id,
                            call_set_id=call_set.id,
                        )
                        self.db.add(call)
                        calls_by_db_id[call_db_id] = call
                        seeded += 1

                    call.variant_id = variant.id
                    call.call_set_id = call_set.id
                    call.genotype_value = genotype_value
                    call.genotype = {"values": genotype_value.split("/")}
                    call.additional_info = {"seeded_for": "reevu-benchmark-alignment"}

        self.db.commit()
        logger.info("Seeded %s demo benchmark-alignment records", seeded)
        return seeded

    def clear(self) -> int:
        from app.models.core import Organization, Study, Trial
        from app.models.germplasm import Germplasm
        from app.models.genotyping import Call, CallSet, Variant, VariantSet
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable, Sample
        from app.models.speed_breeding import SpeedBreedingProtocol

        demo_org = self.db.execute(
            select(Organization).where(Organization.name == DEMO_DATASET_ORG_NAME)
        ).scalar_one_or_none()
        if not demo_org:
            return 0

        org_id = demo_org.id
        cleared = 0

        observation_ids = [
            stable_demo_id("demo_obs", unit_data["unit_name"], variable_name)
            for unit_data in BENCHMARK_UNITS
            for variable_name in unit_data["observations"]
        ]
        unit_ids = [stable_demo_id("demo_unit", unit_data["unit_name"]) for unit_data in BENCHMARK_UNITS]
        sample_ids = [
            stable_demo_id("demo_sample", population_entry["sample_name"])
            for population_entry in BENCHMARK_WHEAT_TRAINING_POPULATION
        ]
        call_set_ids = [
            stable_demo_id("demo_call_set", population_entry["germplasm_name"])
            for population_entry in BENCHMARK_WHEAT_TRAINING_POPULATION
        ]
        call_ids = [
            stable_demo_id("demo_call", population_entry["germplasm_name"], variant_data["name"])
            for population_entry in BENCHMARK_WHEAT_TRAINING_POPULATION
            for variant_data in BENCHMARK_WHEAT_VARIANTS
        ]
        variant_ids = [
            stable_demo_id("demo_variant", variant_data["name"])
            for variant_data in BENCHMARK_WHEAT_VARIANTS
        ]
        variant_set_db_id = stable_demo_id("demo_variant_set", BENCHMARK_WHEAT_VARIANT_SET_NAME)

        if call_ids:
            cleared += (
                self.db.query(Call)
                .filter(
                    Call.organization_id == org_id,
                    Call.call_db_id.in_(call_ids),
                )
                .delete(synchronize_session=False)
            )
        if call_set_ids:
            cleared += (
                self.db.query(CallSet)
                .filter(
                    CallSet.organization_id == org_id,
                    CallSet.call_set_db_id.in_(call_set_ids),
                )
                .delete(synchronize_session=False)
            )
        if sample_ids:
            cleared += (
                self.db.query(Sample)
                .filter(
                    Sample.organization_id == org_id,
                    Sample.sample_db_id.in_(sample_ids),
                )
                .delete(synchronize_session=False)
            )

        if observation_ids:
            cleared += (
                self.db.query(Observation)
                .filter(
                    Observation.organization_id == org_id,
                    Observation.observation_db_id.in_(observation_ids),
                )
                .delete(synchronize_session=False)
            )
        if unit_ids:
            cleared += (
                self.db.query(ObservationUnit)
                .filter(
                    ObservationUnit.organization_id == org_id,
                    ObservationUnit.observation_unit_db_id.in_(unit_ids),
                )
                .delete(synchronize_session=False)
            )

        if variant_ids:
            cleared += (
                self.db.query(Variant)
                .filter(
                    Variant.organization_id == org_id,
                    Variant.variant_db_id.in_(variant_ids),
                )
                .delete(synchronize_session=False)
            )
        cleared += (
            self.db.query(VariantSet)
            .filter(
                VariantSet.organization_id == org_id,
                VariantSet.variant_set_db_id == variant_set_db_id,
            )
            .delete(synchronize_session=False)
        )

        cleared += (
            self.db.query(Study)
            .filter(Study.organization_id == org_id, Study.study_name == BENCHMARK_STUDY_NAME)
            .delete(synchronize_session=False)
        )
        cleared += (
            self.db.query(Trial)
            .filter(Trial.organization_id == org_id, Trial.trial_name == BENCHMARK_TRIAL_NAME)
            .delete(synchronize_session=False)
        )
        cleared += (
            self.db.query(ObservationVariable)
            .filter(
                ObservationVariable.organization_id == org_id,
                ObservationVariable.observation_variable_name == "Drought Tolerance Score",
            )
            .delete(synchronize_session=False)
        )
        cleared += (
            self.db.query(SpeedBreedingProtocol)
            .filter(
                SpeedBreedingProtocol.organization_id == org_id,
                SpeedBreedingProtocol.name.in_([protocol["name"] for protocol in BENCHMARK_PROTOCOLS]),
            )
            .delete(synchronize_session=False)
        )

        germplasm_rows = (
            self.db.query(Germplasm)
            .filter(
                Germplasm.organization_id == org_id,
                Germplasm.germplasm_name.in_(list(BENCHMARK_GERMPLASM_TRAITS.keys())),
            )
            .all()
        )
        for germplasm in germplasm_rows:
            additional_info = dict(germplasm.additional_info or {})
            existing_traits = [
                trait for trait in additional_info.get("traits", []) if isinstance(trait, str) and trait.strip()
            ]
            remaining_traits = sorted(
                set(existing_traits) - set(BENCHMARK_GERMPLASM_TRAITS.get(germplasm.germplasm_name, []))
            )
            if remaining_traits:
                additional_info["traits"] = remaining_traits
                germplasm.additional_info = additional_info
            elif "traits" in additional_info:
                additional_info.pop("traits", None)
                germplasm.additional_info = additional_info or None

        self.db.commit()
        logger.info("Cleared %s demo benchmark-alignment records", cleared)
        return cleared