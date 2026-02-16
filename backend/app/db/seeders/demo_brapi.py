"""
Demo BrAPI Seeder

Seeds demo data for BrAPI endpoints (programs, trials, studies, locations)
for development and testing.
"""

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from .base import BaseSeeder, register_seeder
import logging

logger = logging.getLogger(__name__)


@register_seeder
class DemoBrAPISeeder(BaseSeeder):
    """Seeds demo BrAPI data (programs, trials, studies, locations)"""

    name = "demo_brapi"
    description = "Demo BrAPI data (programs, trials, studies, locations)"

    def seed(self) -> int:
        """Seed demo BrAPI data into database."""
        from app.models.core import Organization, Program, Trial, Study, Location

        total = 0

        # Get Demo Organization
        demo_org = self.db.execute(
            select(Organization).where(Organization.name == "Demo Organization")
        ).scalar_one_or_none()

        if not demo_org:
            logger.warning("Demo Organization not found. Run demo_users seeder first.")
            return 0

        org_id = demo_org.id

        # Seed Locations first (needed for trials/studies)
        locations_data = [
            {
                "location_db_id": f"demo_loc_{uuid.uuid4().hex[:8]}",
                "location_name": "IRRI Research Station",
                "location_type": "Research Station",
                "abbreviation": "IRRI-RS",
                "country_code": "PHL",
                "country_name": "Philippines",
                "altitude": "21",
            },
            {
                "location_db_id": f"demo_loc_{uuid.uuid4().hex[:8]}",
                "location_name": "CRRI Research Farm",
                "location_type": "Research Farm",
                "abbreviation": "CRRI-RF",
                "country_code": "IND",
                "country_name": "India",
                "altitude": "23",
            },
            {
                "location_db_id": f"demo_loc_{uuid.uuid4().hex[:8]}",
                "location_name": "IARI Experimental Farm",
                "location_type": "Experimental Farm",
                "abbreviation": "IARI-EF",
                "country_code": "IND",
                "country_name": "India",
                "altitude": "228",
            },
            {
                "location_db_id": f"demo_loc_{uuid.uuid4().hex[:8]}",
                "location_name": "PAU Research Station",
                "location_type": "Research Station",
                "abbreviation": "PAU-RS",
                "country_code": "IND",
                "country_name": "India",
                "altitude": "247",
            },
        ]

        location_map = {}  # name -> Location object
        for loc_data in locations_data:
            loc = Location(organization_id=org_id, **loc_data)
            self.db.add(loc)
            location_map[loc_data["location_name"]] = loc
            total += 1

        self.db.flush()  # Get IDs for locations
        logger.info(f"Seeded {len(locations_data)} locations")

        # Seed Programs
        programs_data = [
            {
                "program_db_id": f"demo_prog_{uuid.uuid4().hex[:8]}",
                "program_name": "Rice Improvement Program",
                "abbreviation": "RIP",
                "objective": "Develop high-yielding, disease-resistant rice varieties",
            },
            {
                "program_db_id": f"demo_prog_{uuid.uuid4().hex[:8]}",
                "program_name": "Wheat Breeding Program",
                "abbreviation": "WBP",
                "objective": "Develop climate-resilient wheat varieties",
            },
            {
                "program_db_id": f"demo_prog_{uuid.uuid4().hex[:8]}",
                "program_name": "Maize Hybrid Development",
                "abbreviation": "MHD",
                "objective": "Develop high-yielding maize hybrids",
            },
        ]

        program_map = {}  # name -> Program object
        for prog_data in programs_data:
            prog = Program(organization_id=org_id, **prog_data)
            self.db.add(prog)
            program_map[prog_data["program_name"]] = prog
            total += 1

        self.db.flush()  # Get IDs for programs
        logger.info(f"Seeded {len(programs_data)} programs")

        # Seed Trials
        trials_data = [
            {
                "trial_db_id": f"demo_trial_{uuid.uuid4().hex[:8]}",
                "trial_name": "Rice Yield Trial 2024",
                "trial_description": "Multi-location yield trial for advanced rice lines",
                "program_name": "Rice Improvement Program",
                "location_name": "IRRI Research Station",
                "start_date": "2024-06-01",
                "end_date": "2024-11-30",
                "active": True,
            },
            {
                "trial_db_id": f"demo_trial_{uuid.uuid4().hex[:8]}",
                "trial_name": "Wheat Disease Resistance Trial",
                "trial_description": "Screening for rust resistance in wheat germplasm",
                "program_name": "Wheat Breeding Program",
                "location_name": "IARI Experimental Farm",
                "start_date": "2024-11-01",
                "end_date": "2025-04-30",
                "active": True,
            },
            {
                "trial_db_id": f"demo_trial_{uuid.uuid4().hex[:8]}",
                "trial_name": "Maize Hybrid Evaluation 2024",
                "trial_description": "Performance evaluation of new maize hybrids",
                "program_name": "Maize Hybrid Development",
                "location_name": "PAU Research Station",
                "start_date": "2024-06-15",
                "end_date": "2024-10-15",
                "active": False,
            },
        ]

        trial_map = {}  # name -> Trial object
        for trial_data in trials_data:
            program = program_map.get(trial_data.pop("program_name"))
            location = location_map.get(trial_data.pop("location_name"))

            trial = Trial(
                organization_id=org_id,
                program_id=program.id if program else None,
                location_id=location.id if location else None,
                **trial_data
            )
            self.db.add(trial)
            trial_map[trial_data["trial_name"]] = trial
            total += 1

        self.db.flush()  # Get IDs for trials
        logger.info(f"Seeded {len(trials_data)} trials")

        # Seed Studies
        studies_data = [
            {
                "study_db_id": f"demo_study_{uuid.uuid4().hex[:8]}",
                "study_name": "RYT-2024-LOC1",
                "study_description": "Rice Yield Trial at Location 1",
                "study_type": "Yield Trial",
                "trial_name": "Rice Yield Trial 2024",
                "location_name": "IRRI Research Station",
                "start_date": "2024-06-15",
                "end_date": "2024-11-15",
            },
            {
                "study_db_id": f"demo_study_{uuid.uuid4().hex[:8]}",
                "study_name": "RYT-2024-LOC2",
                "study_description": "Rice Yield Trial at Location 2",
                "study_type": "Yield Trial",
                "trial_name": "Rice Yield Trial 2024",
                "location_name": "CRRI Research Farm",
                "start_date": "2024-06-20",
                "end_date": "2024-11-20",
            },
            {
                "study_db_id": f"demo_study_{uuid.uuid4().hex[:8]}",
                "study_name": "WDR-2024-SCREEN",
                "study_description": "Wheat Disease Resistance Screening",
                "study_type": "Disease Screening",
                "trial_name": "Wheat Disease Resistance Trial",
                "location_name": "IARI Experimental Farm",
                "start_date": "2024-11-15",
                "end_date": "2025-04-15",
            },
        ]

        for study_data in studies_data:
            trial = trial_map.get(study_data.pop("trial_name"))
            location = location_map.get(study_data.pop("location_name"))

            study = Study(
                organization_id=org_id,
                trial_id=trial.id if trial else None,
                location_id=location.id if location else None,
                **study_data
            )
            self.db.add(study)
            total += 1

        logger.info(f"Seeded {len(studies_data)} studies")

        self.db.commit()
        return total

    def clear(self) -> int:
        """Clear demo BrAPI data"""
        from app.models.core import Organization, Program, Trial, Study, Location

        total = 0

        # Get Demo Organization
        demo_org = self.db.execute(
            select(Organization).where(Organization.name == "Demo Organization")
        ).scalar_one_or_none()

        if not demo_org:
            return 0

        org_id = demo_org.id

        # Delete in reverse order (studies -> trials -> programs -> locations)
        result = self.db.query(Study).filter(Study.organization_id == org_id).delete()
        total += result

        result = self.db.query(Trial).filter(Trial.organization_id == org_id).delete()
        total += result

        result = self.db.query(Program).filter(Program.organization_id == org_id).delete()
        total += result

        result = self.db.query(Location).filter(Location.organization_id == org_id).delete()
        total += result

        self.db.commit()
        return total
