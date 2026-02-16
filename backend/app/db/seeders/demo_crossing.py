"""
Demo Crossing Seeder

Seeds demo data for crossing projects and planned crosses
into the database for development and testing.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization
from app.models.germplasm import CrossingProject, PlannedCross, Germplasm
from app.models.core import Program, Organization
import logging
import uuid

logger = logging.getLogger(__name__)

# Demo Crossing Projects
DEMO_CROSSING_PROJECTS = [
    {
        "crossing_project_name": "Rice Yield Improvement 2025",
        "crossing_project_description": "Crossing project to improve yield in rice through elite x elite crosses",
        "common_crop_name": "Rice",
    },
    {
        "crossing_project_name": "Wheat Disease Resistance",
        "crossing_project_description": "Introgression of disease resistance genes from wild relatives",
        "common_crop_name": "Wheat",
    },
    {
        "crossing_project_name": "Maize Drought Tolerance",
        "crossing_project_description": "Development of drought tolerant maize hybrids for rainfed areas",
        "common_crop_name": "Maize",
    },
]

# Demo Planned Crosses
DEMO_PLANNED_CROSSES = [
    {
        "planned_cross_name": "IR64 x Swarna",
        "cross_type": "BIPARENTAL",
        "status": "TODO",
        "parent1_name": "IR64",
        "parent1_type": "FEMALE",
        "parent2_name": "Swarna",
        "parent2_type": "MALE",
        "project_name": "Rice Yield Improvement 2025",
    },
    {
        "planned_cross_name": "IR64 x Pusa Basmati 1121",
        "cross_type": "BIPARENTAL",
        "status": "DONE",
        "parent1_name": "IR64",
        "parent1_type": "FEMALE",
        "parent2_name": "Pusa Basmati 1121",
        "parent2_type": "MALE",
        "project_name": "Rice Yield Improvement 2025",
    },
    {
        "planned_cross_name": "HD2967 x PBW343",
        "cross_type": "BIPARENTAL",
        "status": "TODO",
        "parent1_name": "HD2967",
        "parent1_type": "FEMALE",
        "parent2_name": "PBW343",
        "parent2_type": "MALE",
        "project_name": "Wheat Disease Resistance",
    },
    {
        "planned_cross_name": "Swarna Self",
        "cross_type": "SELF",
        "status": "TODO",
        "parent1_name": "Swarna",
        "parent1_type": "SELF",
        "parent2_name": None,
        "parent2_type": None,
        "project_name": "Rice Yield Improvement 2025",
    },
]


@register_seeder
class DemoCrossingSeeder(BaseSeeder):
    """Seeds demo crossing data (projects, planned crosses)"""

    name = "demo_crossing"
    description = "Demo crossing data (projects, planned crosses)"

    def seed(self) -> int:
        """Seed demo crossing data into the database."""
        org = get_or_create_demo_organization(self.db)
        total = 0

        # Get germplasm IDs for linking
        germplasm_ids = {}
        for germ in self.db.query(Germplasm).filter(Germplasm.organization_id == org.id).all():
            germplasm_ids[germ.germplasm_name] = germ.id

        # Seed Crossing Projects
        project_ids = {}
        for data in DEMO_CROSSING_PROJECTS:
            existing = self.db.query(CrossingProject).filter(
                CrossingProject.crossing_project_name == data["crossing_project_name"]
            ).first()
            if existing:
                project_ids[data["crossing_project_name"]] = existing.id
                continue

            project = CrossingProject(
                organization_id=org.id,
                crossing_project_db_id=f"cp_{uuid.uuid4().hex[:8]}",
                crossing_project_name=data["crossing_project_name"],
                crossing_project_description=data.get("crossing_project_description"),
                common_crop_name=data.get("common_crop_name"),
            )
            self.db.add(project)
            self.db.flush()
            project_ids[data["crossing_project_name"]] = project.id
            total += 1

        # Seed Planned Crosses
        for data in DEMO_PLANNED_CROSSES:
            existing = self.db.query(PlannedCross).filter(
                PlannedCross.planned_cross_name == data["planned_cross_name"]
            ).first()
            if existing:
                continue

            cross = PlannedCross(
                organization_id=org.id,
                crossing_project_id=project_ids.get(data.get("project_name")),
                planned_cross_db_id=f"pc_{uuid.uuid4().hex[:8]}",
                planned_cross_name=data["planned_cross_name"],
                cross_type=data.get("cross_type", "BIPARENTAL"),
                status=data.get("status", "TODO"),
                parent1_db_id=germplasm_ids.get(data.get("parent1_name")),
                parent1_type=data.get("parent1_type"),
                parent2_db_id=germplasm_ids.get(data.get("parent2_name")) if data.get("parent2_name") else None,
                parent2_type=data.get("parent2_type"),
            )
            self.db.add(cross)
            total += 1

        self.db.commit()
        logger.info(f"Seeded {total} crossing records")
        return total

    def clear(self) -> int:
        """Clear demo crossing data"""
        org = self.db.query(Organization).filter(
            Organization.name == "Demo Organization"
        ).first()
        if not org:
            return 0

        total = 0

        # Delete planned crosses first (foreign key)
        count = self.db.query(PlannedCross).filter(
            PlannedCross.organization_id == org.id
        ).delete()
        total += count

        # Delete crossing projects
        count = self.db.query(CrossingProject).filter(
            CrossingProject.organization_id == org.id
        ).delete()
        total += count

        self.db.commit()
        logger.info(f"Cleared {total} crossing records")
        return total
