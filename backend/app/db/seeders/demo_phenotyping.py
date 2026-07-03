"""
Demo Phenotyping Seeder

Seeds demo phenotyping data (traits, observations, samples, etc.) into the Demo Organization.
"""

import logging

from app.core.demo_dataset import (
    DEMO_DATASET_ORG_NAME,
    stable_demo_float,
    stable_demo_id,
)

from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization


logger = logging.getLogger(__name__)

# Demo observation variables (traits)
DEMO_VARIABLES = [
    {
        "observation_variable_name": "Plant Height",
        "common_crop_name": "Rice",
        "trait_name": "Plant Height",
        "trait_description": "Height of the plant from ground to tip of tallest panicle",
        "trait_class": "Morphological",
        "method_name": "Measurement",
        "method_description": "Measure from ground to tip using measuring tape",
        "scale_name": "cm",
        "data_type": "Numerical",
        "status": "active",
    },
    {
        "observation_variable_name": "Days to Flowering",
        "common_crop_name": "Rice",
        "trait_name": "Days to Flowering",
        "trait_description": "Number of days from sowing to 50% flowering",
        "trait_class": "Phenological",
        "method_name": "Counting",
        "method_description": "Count days from sowing date to 50% flowering",
        "scale_name": "days",
        "data_type": "Numerical",
        "status": "active",
    },
    {
        "observation_variable_name": "Grain Yield",
        "common_crop_name": "Rice",
        "trait_name": "Grain Yield",
        "trait_description": "Total grain weight per plot at 14% moisture",
        "trait_class": "Agronomic",
        "method_name": "Weighing",
        "method_description": "Harvest, thresh, dry to 14% moisture, weigh",
        "scale_name": "kg/ha",
        "data_type": "Numerical",
        "status": "active",
    },
    {
        "observation_variable_name": "Thousand Grain Weight",
        "common_crop_name": "Wheat",
        "trait_name": "Thousand Grain Weight",
        "trait_description": "Weight of 1000 grains",
        "trait_class": "Agronomic",
        "method_name": "Weighing",
        "method_description": "Count 1000 grains and weigh",
        "scale_name": "g",
        "data_type": "Numerical",
        "status": "active",
    },
    {
        "observation_variable_name": "Disease Score",
        "common_crop_name": "Rice",
        "trait_name": "Blast Resistance",
        "trait_description": "Visual score for blast disease resistance",
        "trait_class": "Disease",
        "method_name": "Visual Scoring",
        "method_description": "Score on 1-9 scale (1=resistant, 9=susceptible)",
        "scale_name": "1-9 scale",
        "data_type": "Ordinal",
        "valid_values": {"categories": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
        "status": "active",
    },
]

# Demo observation units
DEMO_UNITS = [
    {
        "observation_unit_name": "Plot-001-A",
        "observation_level": "plot",
        "position_coordinate_x": "1",
        "position_coordinate_y": "A",
    },
    {
        "observation_unit_name": "Plot-001-B",
        "observation_level": "plot",
        "position_coordinate_x": "1",
        "position_coordinate_y": "B",
    },
    {
        "observation_unit_name": "Plot-002-A",
        "observation_level": "plot",
        "position_coordinate_x": "2",
        "position_coordinate_y": "A",
    },
    {
        "observation_unit_name": "Plot-002-B",
        "observation_level": "plot",
        "position_coordinate_x": "2",
        "position_coordinate_y": "B",
    },
    {
        "observation_unit_name": "Plot-003-A",
        "observation_level": "plot",
        "position_coordinate_x": "3",
        "position_coordinate_y": "A",
    },
]

# Demo samples
DEMO_SAMPLES = [
    {"sample_name": "SAMPLE-001", "sample_type": "Leaf", "tissue_type": "Leaf tissue"},
    {"sample_name": "SAMPLE-002", "sample_type": "Leaf", "tissue_type": "Leaf tissue"},
    {"sample_name": "SAMPLE-003", "sample_type": "Seed", "tissue_type": "Seed"},
    {"sample_name": "SAMPLE-004", "sample_type": "DNA", "tissue_type": "Extracted DNA"},
]

# Demo events
DEMO_EVENTS = [
    {"event_type": "Planting", "event_description": "Seeds planted in field", "date": "2025-06-15"},
    {
        "event_type": "Fertilization",
        "event_description": "NPK fertilizer applied",
        "date": "2025-07-01",
    },
    {"event_type": "Irrigation", "event_description": "Field irrigated", "date": "2025-07-15"},
    {"event_type": "Harvest", "event_description": "Plots harvested", "date": "2025-10-15"},
]


@register_seeder
class DemoPhenotypingSeeder(BaseSeeder):
    """Seeds demo phenotyping data into Demo Organization"""

    name = "demo_phenotyping"
    description = "Demo phenotyping data (traits, observations, samples, events)"

    def seed(self) -> int:
        """Seed demo phenotyping data into the database."""
        from app.models.phenotyping import (
            Event,
            Observation,
            ObservationUnit,
            ObservationVariable,
            Sample,
        )

        org = get_or_create_demo_organization(self.db)
        count = 0

        # Seed observation variables (traits)
        variable_refs = []
        for data in DEMO_VARIABLES:
            existing = (
                self.db.query(ObservationVariable)
                .filter(
                    ObservationVariable.observation_variable_name
                    == data["observation_variable_name"],
                    ObservationVariable.organization_id == org.id,
                )
                .first()
            )

            if existing:
                variable_refs.append((existing.id, data["observation_variable_name"]))
                continue

            var = ObservationVariable(
                organization_id=org.id,
                observation_variable_db_id=stable_demo_id(
                    "demo_var", data["observation_variable_name"]
                ),
                **data,
            )
            self.db.add(var)
            self.db.flush()
            variable_refs.append((var.id, data["observation_variable_name"]))
            count += 1

        # Seed observation units
        unit_refs = []
        for data in DEMO_UNITS:
            existing = (
                self.db.query(ObservationUnit)
                .filter(
                    ObservationUnit.observation_unit_name == data["observation_unit_name"],
                    ObservationUnit.organization_id == org.id,
                )
                .first()
            )

            if existing:
                unit_refs.append((existing.id, data["observation_unit_name"]))
                continue

            unit = ObservationUnit(
                organization_id=org.id,
                observation_unit_db_id=stable_demo_id(
                    "demo_unit", data["observation_unit_name"]
                ),
                **data,
            )
            self.db.add(unit)
            self.db.flush()
            unit_refs.append((unit.id, data["observation_unit_name"]))
            count += 1

        # Seed samples
        for i, data in enumerate(DEMO_SAMPLES):
            existing = (
                self.db.query(Sample)
                .filter(Sample.sample_name == data["sample_name"], Sample.organization_id == org.id)
                .first()
            )

            if existing:
                continue

            sample = Sample(
                organization_id=org.id,
                sample_db_id=stable_demo_id("demo_sample", data["sample_name"]),
                observation_unit_id=unit_refs[i % len(unit_refs)][0] if unit_refs else None,
                **data,
            )
            self.db.add(sample)
            count += 1

        # Seed events
        for data in DEMO_EVENTS:
            existing = (
                self.db.query(Event)
                .filter(
                    Event.event_type == data["event_type"],
                    Event.date == data["date"],
                    Event.organization_id == org.id,
                )
                .first()
            )

            if existing:
                continue

            event = Event(
                organization_id=org.id,
                event_db_id=stable_demo_id("demo_event", data["event_type"], data["date"]),
                **data,
            )
            self.db.add(event)
            count += 1

        # Seed some observations
        for unit_id, unit_name in unit_refs[:3]:
            for variable_id, variable_name in variable_refs[:3]:
                existing = (
                    self.db.query(Observation)
                    .filter(
                        Observation.observation_unit_id == unit_id,
                        Observation.observation_variable_id == variable_id,
                        Observation.organization_id == org.id,
                    )
                    .first()
                )

                if existing:
                    continue

                obs = Observation(
                    organization_id=org.id,
                    observation_db_id=stable_demo_id("demo_obs", unit_name, variable_name),
                    observation_unit_id=unit_id,
                    observation_variable_id=variable_id,
                    value=str(
                        stable_demo_float(50, 150, unit_name, variable_name, digits=2)
                    ),
                    collector="Demo User",
                    observation_time_stamp="2025-08-15T10:00:00Z",
                )
                self.db.add(obs)
                count += 1

        self.db.commit()
        logger.info(f"Seeded {count} phenotyping records into Demo Organization")
        return count

    def clear(self) -> int:
        """Clear demo phenotyping data from Demo Organization only"""
        from app.models.core import Organization
        from app.models.phenotyping import (
            Event,
            Image,
            Observation,
            ObservationUnit,
            ObservationVariable,
            Sample,
        )

        org = self.db.query(Organization).filter(Organization.name == DEMO_DATASET_ORG_NAME).first()
        if not org:
            return 0

        count = 0
        # Delete in order due to foreign keys
        count += self.db.query(Observation).filter(Observation.organization_id == org.id).delete()
        count += self.db.query(Image).filter(Image.organization_id == org.id).delete()
        count += self.db.query(Sample).filter(Sample.organization_id == org.id).delete()
        count += self.db.query(Event).filter(Event.organization_id == org.id).delete()
        count += (
            self.db.query(ObservationUnit)
            .filter(ObservationUnit.organization_id == org.id)
            .delete()
        )
        count += (
            self.db.query(ObservationVariable)
            .filter(ObservationVariable.organization_id == org.id)
            .delete()
        )

        self.db.commit()
        logger.info(f"Cleared {count} phenotyping records from Demo Organization")
        return count
