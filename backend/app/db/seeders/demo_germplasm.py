"""
Demo Germplasm Seeder

Seeds demo germplasm data into the "Demo Organization" for sandboxed demo access.
Demo users (demo@bijmantra.org) log into this organization and see only demo data.
Production organizations are completely isolated.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
import logging
import uuid

logger = logging.getLogger(__name__)

# Demo germplasm data
DEMO_GERMPLASM = [
    {
        "germplasm_name": "IR64",
        "species": "Oryza sativa",
        "genus": "Oryza",
        "common_crop_name": "Rice",
        "country_of_origin_code": "PHL",
        "accession_number": "DEMO-IRRI-001",
        "institute_code": "IRRI",
        "institute_name": "International Rice Research Institute",
        "biological_status_of_accession_code": "500",
        "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
    },
    {
        "germplasm_name": "Swarna",
        "species": "Oryza sativa",
        "genus": "Oryza",
        "common_crop_name": "Rice",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-CRRI-001",
        "institute_code": "CRRI",
        "institute_name": "Central Rice Research Institute",
        "biological_status_of_accession_code": "500",
        "pedigree": "Vasistha/Mahsuri",
    },
    {
        "germplasm_name": "HD2967",
        "species": "Triticum aestivum",
        "genus": "Triticum",
        "common_crop_name": "Wheat",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-IARI-001",
        "institute_code": "IARI",
        "institute_name": "Indian Agricultural Research Institute",
        "biological_status_of_accession_code": "500",
        "pedigree": "ALD/COC//URES/HD2160M/HD2278",
    },
    {
        "germplasm_name": "PBW343",
        "species": "Triticum aestivum",
        "genus": "Triticum",
        "common_crop_name": "Wheat",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-PAU-001",
        "institute_code": "PAU",
        "institute_name": "Punjab Agricultural University",
        "biological_status_of_accession_code": "500",
    },
    {
        "germplasm_name": "DH86",
        "species": "Zea mays",
        "genus": "Zea",
        "common_crop_name": "Maize",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-DMR-001",
        "institute_code": "DMR",
        "institute_name": "Directorate of Maize Research",
        "biological_status_of_accession_code": "500",
    },
    {
        "germplasm_name": "Pusa Basmati 1121",
        "species": "Oryza sativa",
        "genus": "Oryza",
        "common_crop_name": "Rice",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-IARI-002",
        "institute_code": "IARI",
        "institute_name": "Indian Agricultural Research Institute",
        "biological_status_of_accession_code": "500",
    },
    {
        "germplasm_name": "Kalyan Sona",
        "species": "Triticum aestivum",
        "genus": "Triticum",
        "common_crop_name": "Wheat",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-IARI-003",
        "institute_code": "IARI",
        "institute_name": "Indian Agricultural Research Institute",
        "biological_status_of_accession_code": "500",
    },
    {
        "germplasm_name": "Sharbati",
        "species": "Triticum aestivum",
        "genus": "Triticum",
        "common_crop_name": "Wheat",
        "country_of_origin_code": "IND",
        "accession_number": "DEMO-MP-001",
        "institute_code": "JNKVV",
        "institute_name": "Jawaharlal Nehru Krishi Vishwa Vidyalaya",
        "biological_status_of_accession_code": "500",
    },
]


def get_or_create_demo_organization(db: Session):
    """Get or create the Demo Organization for sandboxed demo data"""
    from app.models.core import Organization

    org = db.query(Organization).filter(Organization.name == "Demo Organization").first()
    if not org:
        org = Organization(
            name="Demo Organization",
            description="Sandboxed demo organization for showcasing Bijmantra. Data here is isolated from production.",
            contact_email="demo@bijmantra.org",
            website="https://bijmantra.org/demo",
            is_active=True
        )
        db.add(org)
        db.flush()
        logger.info(f"Created Demo Organization with id={org.id}")
    return org


@register_seeder
class DemoGermplasmSeeder(BaseSeeder):
    """Seeds demo germplasm data into Demo Organization"""

    name = "demo_germplasm"
    description = "Demo germplasm entries (Rice, Wheat, Maize) in Demo Organization"

    def seed(self) -> int:
        """Seed demo germplasm data into the database."""
        from app.models.germplasm import Germplasm

        # Get or create demo organization
        org = get_or_create_demo_organization(self.db)

        count = 0

        # Pre-fetch existing accession numbers to avoid N+1 query
        accession_numbers = [data["accession_number"] for data in DEMO_GERMPLASM if data.get("accession_number")]
        existing_accession_numbers = set()

        if accession_numbers:
            existing_records = self.db.query(Germplasm.accession_number).filter(
                Germplasm.accession_number.in_(accession_numbers)
            ).all()
            existing_accession_numbers = {r[0] for r in existing_records}

        for data in DEMO_GERMPLASM:
            # Check if germplasm already exists (by accession number)
            if data.get("accession_number") in existing_accession_numbers:
                logger.debug(f"Germplasm {data['germplasm_name']} already exists, skipping")
                continue

            # Generate unique germplasm_db_id
            germplasm_db_id = f"demo_germplasm_{uuid.uuid4().hex[:8]}"

            germplasm = Germplasm(
                organization_id=org.id,
                germplasm_db_id=germplasm_db_id,
                germplasm_name=data["germplasm_name"],
                species=data.get("species"),
                genus=data.get("genus"),
                common_crop_name=data.get("common_crop_name"),
                country_of_origin_code=data.get("country_of_origin_code"),
                accession_number=data.get("accession_number"),
                institute_code=data.get("institute_code"),
                institute_name=data.get("institute_name"),
                biological_status_of_accession_code=data.get("biological_status_of_accession_code"),
                pedigree=data.get("pedigree"),
                synonyms=[],
            )
            self.db.add(germplasm)
            count += 1
            logger.debug(f"Added germplasm: {data['germplasm_name']}")

        self.db.commit()
        logger.info(f"Seeded {count} germplasm entries into Demo Organization")
        return count

    def clear(self) -> int:
        """Clear demo germplasm data from Demo Organization only"""
        from app.models.germplasm import Germplasm
        from app.models.core import Organization

        # Get demo organization
        org = self.db.query(Organization).filter(Organization.name == "Demo Organization").first()
        if not org:
            return 0

        # Delete germplasm from demo organization only
        count = self.db.query(Germplasm).filter(
            Germplasm.organization_id == org.id
        ).delete()

        self.db.commit()
        logger.info(f"Cleared {count} germplasm entries from Demo Organization")
        return count
