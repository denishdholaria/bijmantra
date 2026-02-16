"""
Demo Field Operations Seeder
Seeds nursery management and field book data for Demo Organization
"""
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.core import Organization
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_seeder
class DemoFieldOperationsSeeder(BaseSeeder):
    """Seeds nursery and field book demo data"""

    name = "demo_field_operations"
    priority = 65  # After stress resistance

    def seed(self) -> int:
        """Seed field operations data"""
        from app.models.field_operations import (
            NurseryLocation, SeedlingBatch, FieldBookStudy,
            FieldBookTrait, FieldBookEntry, FieldBookObservation,
            BatchStatus
        )

        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()

        if not demo_org:
            logger.warning("Demo Organization not found, skipping field operations seeding")
            return 0

        count = 0
        org_id = demo_org.id
        today = date.today()

        # Check if already seeded
        from app.models.field_operations import NurseryLocation
        existing = self.db.query(NurseryLocation).filter(
            NurseryLocation.organization_id == org_id
        ).first()
        if existing:
            logger.info("Field operations data already seeded")
            return 0

        # ============================================
        # NURSERY LOCATIONS
        # ============================================
        locations_data = [
            {"name": "Greenhouse A", "location_type": "greenhouse", "capacity": 5000, "description": "Main greenhouse for elite materials"},
            {"name": "Greenhouse B", "location_type": "greenhouse", "capacity": 3000, "description": "Secondary greenhouse"},
            {"name": "Greenhouse C", "location_type": "greenhouse", "capacity": 2000, "description": "Quarantine greenhouse"},
            {"name": "Field A", "location_type": "field", "capacity": 10000, "description": "Main field nursery"},
            {"name": "Field B", "location_type": "field", "capacity": 8000, "description": "Secondary field nursery"},
            {"name": "Nursery Shed", "location_type": "shed", "capacity": 1000, "description": "Covered nursery area"},
        ]

        location_map = {}
        for data in locations_data:
            loc = NurseryLocation(
                organization_id=org_id,
                **data
            )
            self.db.add(loc)
            self.db.flush()  # Get the auto-generated ID
            location_map[data["name"]] = loc.id
            count += 1

        # ============================================
        # SEEDLING BATCHES
        # ============================================
        batches_data = [
            {
                "batch_code": "NB001",
                "germplasm_name": "Elite Variety 2024",
                "sowing_date": today - timedelta(days=30),
                "expected_transplant_date": today,
                "quantity_sown": 500,
                "quantity_germinated": 475,
                "quantity_healthy": 450,
                "status": BatchStatus.READY,
                "location_name": "Greenhouse A",
            },
            {
                "batch_code": "NB002",
                "germplasm_name": "High Yield Line A",
                "sowing_date": today - timedelta(days=25),
                "expected_transplant_date": today + timedelta(days=5),
                "quantity_sown": 300,
                "quantity_germinated": 280,
                "quantity_healthy": 265,
                "status": BatchStatus.GROWING,
                "location_name": "Greenhouse A",
            },
            {
                "batch_code": "NB003",
                "germplasm_name": "Disease Resistant B",
                "sowing_date": today - timedelta(days=20),
                "expected_transplant_date": today + timedelta(days=10),
                "quantity_sown": 400,
                "quantity_germinated": 350,
                "quantity_healthy": 340,
                "status": BatchStatus.GERMINATING,
                "location_name": "Greenhouse B",
            },
            {
                "batch_code": "NB004",
                "germplasm_name": "Test Line 001",
                "sowing_date": today - timedelta(days=3),
                "expected_transplant_date": today + timedelta(days=27),
                "quantity_sown": 200,
                "quantity_germinated": 0,
                "quantity_healthy": 0,
                "status": BatchStatus.SOWING,
                "location_name": "Greenhouse B",
            },
            {
                "batch_code": "NB005",
                "germplasm_name": "Variety 2023",
                "sowing_date": today - timedelta(days=45),
                "expected_transplant_date": today - timedelta(days=15),
                "actual_transplant_date": today - timedelta(days=14),
                "quantity_sown": 600,
                "quantity_germinated": 580,
                "quantity_healthy": 560,
                "quantity_transplanted": 550,
                "status": BatchStatus.TRANSPLANTED,
                "location_name": "Field A",
            },
        ]

        for data in batches_data:
            location_name = data.pop("location_name")
            batch = SeedlingBatch(
                organization_id=org_id,
                location_id=location_map.get(location_name),
                **data
            )
            self.db.add(batch)
            count += 1

        # ============================================
        # FIELD BOOK STUDIES
        # ============================================
        studies_data = [
            {
                "study_code": "STD-001",
                "name": "Rice Yield Trial 2025 Kharif",
                "location": "NRRI Cuttack",
                "season": "Kharif 2025",
                "design": "RCBD",
                "replications": 3,
                "total_entries": 9,
                "total_traits": 4,
            },
            {
                "study_code": "STD-002",
                "name": "Wheat Disease Screening",
                "location": "IARI Delhi",
                "season": "Rabi 2024-25",
                "design": "Augmented",
                "replications": 2,
                "total_entries": 50,
                "total_traits": 6,
            },
        ]

        study_map = {}
        for data in studies_data:
            study = FieldBookStudy(
                organization_id=org_id,
                is_active=True,
                **data
            )
            self.db.add(study)
            self.db.flush()  # Get the auto-generated ID
            study_map[data["study_code"]] = study.id
            count += 1

        # ============================================
        # FIELD BOOK TRAITS (for STD-001)
        # ============================================
        traits_data = [
            {"trait_code": "plant_height", "name": "Plant Height", "unit": "cm", "min_value": 0, "max_value": 300, "step": 1, "display_order": 1},
            {"trait_code": "days_to_flowering", "name": "Days to Flowering", "unit": "days", "min_value": 0, "max_value": 200, "step": 1, "display_order": 2},
            {"trait_code": "disease_score", "name": "Disease Score", "unit": "", "min_value": 1, "max_value": 9, "step": 1, "display_order": 3},
            {"trait_code": "yield", "name": "Yield", "unit": "kg/ha", "min_value": 0, "max_value": 20000, "step": 10, "display_order": 4},
        ]

        trait_map = {}
        study_id = study_map["STD-001"]
        for data in traits_data:
            trait = FieldBookTrait(
                organization_id=org_id,
                study_id=study_id,
                data_type="numeric",
                **data
            )
            self.db.add(trait)
            self.db.flush()  # Get the auto-generated ID
            trait_map[data["trait_code"]] = trait.id
            count += 1

        # ============================================
        # FIELD BOOK ENTRIES (for STD-001)
        # ============================================
        germplasm_names = ["Elite Variety 2024", "High Yield Line A", "Disease Resistant B"]
        entries_data = []
        entry_map = {}

        for rep in range(1, 4):  # 3 replications
            for col, germ in enumerate(germplasm_names, 1):
                plot_id = f"A-{rep:02d}-{col:02d}"
                entries_data.append({
                    "plot_id": plot_id,
                    "germplasm_name": germ,
                    "replication": f"R{rep}",
                    "row": rep,
                    "column": col,
                })

        for data in entries_data:
            entry = FieldBookEntry(
                organization_id=org_id,
                study_id=study_id,
                **data
            )
            self.db.add(entry)
            self.db.flush()  # Get the auto-generated ID
            entry_map[data["plot_id"]] = entry.id
            count += 1

        # ============================================
        # FIELD BOOK OBSERVATIONS (partial data for demo)
        # ============================================
        # Only first 4 plots have observations
        observations_data = [
            {"plot_id": "A-01-01", "trait_code": "plant_height", "value": 95},
            {"plot_id": "A-01-01", "trait_code": "days_to_flowering", "value": 65},
            {"plot_id": "A-01-01", "trait_code": "disease_score", "value": 2},
            {"plot_id": "A-01-02", "trait_code": "plant_height", "value": 102},
            {"plot_id": "A-01-02", "trait_code": "days_to_flowering", "value": 68},
            {"plot_id": "A-01-02", "trait_code": "disease_score", "value": 3},
            {"plot_id": "A-01-03", "trait_code": "plant_height", "value": 88},
            {"plot_id": "A-01-03", "trait_code": "days_to_flowering", "value": 62},
            {"plot_id": "A-01-03", "trait_code": "disease_score", "value": 1},
            {"plot_id": "A-02-01", "trait_code": "plant_height", "value": 92},
            {"plot_id": "A-02-01", "trait_code": "days_to_flowering", "value": 64},
            {"plot_id": "A-02-01", "trait_code": "disease_score", "value": 2},
        ]

        for data in observations_data:
            obs = FieldBookObservation(
                organization_id=org_id,
                study_id=study_id,
                entry_id=entry_map[data["plot_id"]],
                trait_id=trait_map[data["trait_code"]],
                value_numeric=data["value"],
                observation_timestamp=datetime.now(timezone.utc) - timedelta(days=5),
            )
            self.db.add(obs)
            count += 1

        self.db.commit()
        logger.info(f"Seeded {count} field operations records")
        return count

    def clear(self) -> int:
        """Clear field operations data"""
        from app.models.field_operations import (
            NurseryLocation, SeedlingBatch, FieldBookStudy,
            FieldBookTrait, FieldBookEntry, FieldBookObservation
        )

        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()

        if not demo_org:
            return 0

        count = 0

        # Delete in order (children first)
        count += self.db.query(FieldBookObservation).filter(
            FieldBookObservation.organization_id == demo_org.id
        ).delete()

        count += self.db.query(FieldBookEntry).filter(
            FieldBookEntry.organization_id == demo_org.id
        ).delete()

        count += self.db.query(FieldBookTrait).filter(
            FieldBookTrait.organization_id == demo_org.id
        ).delete()

        count += self.db.query(FieldBookStudy).filter(
            FieldBookStudy.organization_id == demo_org.id
        ).delete()

        count += self.db.query(SeedlingBatch).filter(
            SeedlingBatch.organization_id == demo_org.id
        ).delete()

        count += self.db.query(NurseryLocation).filter(
            NurseryLocation.organization_id == demo_org.id
        ).delete()

        self.db.commit()
        return count
