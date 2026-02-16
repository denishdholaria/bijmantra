"""
Demo BrAPI Core Seeder

Seeds demo data for BrAPI Core entities (Seasons, Ontologies, Lists, People)
into the database for development and testing.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
from .demo_germplasm import get_or_create_demo_organization
from app.models.core import Organization, Season, Ontology, List as ListModel, Person
import logging
import uuid

logger = logging.getLogger(__name__)

# Demo Seasons
DEMO_SEASONS = [
    {"season_name": "Spring 2024", "year": 2024},
    {"season_name": "Summer 2024", "year": 2024},
    {"season_name": "Kharif 2024", "year": 2024},
    {"season_name": "Rabi 2024-25", "year": 2024},
    {"season_name": "Winter 2024", "year": 2024},
    {"season_name": "Spring 2025", "year": 2025},
    {"season_name": "Wet Season 2024", "year": 2024},
    {"season_name": "Dry Season 2025", "year": 2025},
]

# Demo People
DEMO_PEOPLE = [
    {
        "first_name": "Raj",
        "last_name": "Sharma",
        "email_address": "raj.sharma@example.org",
        "phone_number": "+91-9876543210",
        "mailing_address": "ICAR-IARI, New Delhi, India",
    },
    {
        "first_name": "Priya",
        "last_name": "Patel",
        "middle_name": "K",
        "email_address": "priya.patel@example.org",
        "phone_number": "+91-9876543211",
        "mailing_address": "ICRISAT, Hyderabad, India",
    },
    {
        "first_name": "Amit",
        "last_name": "Kumar",
        "email_address": "amit.kumar@example.org",
        "phone_number": "+91-9876543212",
        "mailing_address": "PAU, Ludhiana, India",
    },
    {
        "first_name": "Sunita",
        "last_name": "Devi",
        "email_address": "sunita.devi@example.org",
        "phone_number": "+91-9876543213",
        "mailing_address": "NBPGR, New Delhi, India",
    },
    {
        "first_name": "Vikram",
        "last_name": "Singh",
        "middle_name": "J",
        "email_address": "vikram.singh@example.org",
        "phone_number": "+91-9876543214",
        "mailing_address": "CIMMYT, Mexico",
    },
]

# Demo Ontologies
DEMO_ONTOLOGIES = [
    {
        "ontology_name": "Crop Ontology",
        "description": "Crop Ontology for agricultural traits and phenotypes",
        "authors": "Crop Ontology Consortium",
        "version": "2024.1",
        "licence": "CC BY 4.0",
        "documentation_url": "https://cropontology.org",
    },
    {
        "ontology_name": "Plant Trait Ontology",
        "description": "Ontology for plant traits and characteristics",
        "authors": "Plant Ontology Consortium",
        "version": "2024.2",
        "licence": "CC BY 4.0",
        "documentation_url": "https://planteome.org",
    },
    {
        "ontology_name": "Gene Ontology",
        "description": "Ontology for gene functions and processes",
        "authors": "Gene Ontology Consortium",
        "version": "2024.12",
        "licence": "CC BY 4.0",
        "documentation_url": "http://geneontology.org",
    },
    {
        "ontology_name": "Rice Ontology",
        "description": "Ontology specific to rice traits (CO_320)",
        "authors": "IRRI",
        "version": "7.0",
        "licence": "CC BY 4.0",
        "documentation_url": "https://cropontology.org/term/CO_320",
    },
    {
        "ontology_name": "Wheat Ontology",
        "description": "Ontology specific to wheat traits (CO_321)",
        "authors": "CIMMYT",
        "version": "5.0",
        "licence": "CC BY 4.0",
        "documentation_url": "https://cropontology.org/term/CO_321",
    },
    {
        "ontology_name": "Maize Ontology",
        "description": "Ontology specific to maize traits (CO_322)",
        "authors": "CIMMYT",
        "version": "4.0",
        "licence": "CC BY 4.0",
        "documentation_url": "https://cropontology.org/term/CO_322",
    },
]

# Demo Lists
DEMO_LISTS = [
    {
        "list_name": "Elite Germplasm 2024",
        "list_description": "Top performing germplasm from 2024 trials",
        "list_type": "germplasm",
        "list_size": 25,
        "list_owner_name": "Dr. Sharma",
        "data": ["IR64", "Swarna", "MTU1010", "BPT5204", "Samba Mahsuri"],
    },
    {
        "list_name": "Disease Resistant Lines",
        "list_description": "Germplasm with confirmed disease resistance",
        "list_type": "germplasm",
        "list_size": 15,
        "list_owner_name": "Dr. Patel",
        "data": ["IR64-BB", "IRBB60", "Improved Samba Mahsuri"],
    },
    {
        "list_name": "Yield Trial Entries 2025",
        "list_description": "Entries selected for 2025 yield trials",
        "list_type": "germplasm",
        "list_size": 50,
        "list_owner_name": "Dr. Kumar",
        "data": [],
    },
    {
        "list_name": "Priority Markers",
        "list_description": "High-priority markers for MAS",
        "list_type": "markers",
        "list_size": 10,
        "list_owner_name": "Dr. Singh",
        "data": ["xa21", "Xa4", "Pi54", "Sub1A", "qDTY1.1"],
    },
    {
        "list_name": "Active Programs",
        "list_description": "Currently active breeding programs",
        "list_type": "programs",
        "list_size": 5,
        "list_owner_name": "Admin",
        "data": ["RIP", "WBP", "MHD"],
    },
]


@register_seeder
class DemoCoreSeeder(BaseSeeder):
    """Seeds demo BrAPI Core data (seasons, ontologies, lists, people)"""

    name = "demo_core"
    description = "Demo BrAPI Core data (seasons, ontologies, lists, people)"

    def seed(self) -> int:
        """Seed demo BrAPI Core data into the database."""
        # Get or create demo organization
        org = get_or_create_demo_organization(self.db)
        total = 0

        # Seed People
        for data in DEMO_PEOPLE:
            # Check if already exists
            existing = self.db.query(Person).filter(
                Person.email_address == data["email_address"]
            ).first()
            if existing:
                continue

            person = Person(
                organization_id=org.id,
                person_db_id=f"person_{data['last_name'].lower()}_{uuid.uuid4().hex[:8]}",
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                middle_name=data.get("middle_name"),
                email_address=data.get("email_address"),
                phone_number=data.get("phone_number"),
                mailing_address=data.get("mailing_address"),
            )
            self.db.add(person)
            total += 1

        # Seed Seasons
        for data in DEMO_SEASONS:
            existing = self.db.query(Season).filter(
                Season.season_name == data["season_name"]
            ).first()
            if existing:
                continue

            season = Season(
                organization_id=org.id,
                season_db_id=f"season_{data['season_name'].lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
                season_name=data["season_name"],
                year=data["year"],
            )
            self.db.add(season)
            total += 1

        # Seed Ontologies
        for data in DEMO_ONTOLOGIES:
            existing = self.db.query(Ontology).filter(
                Ontology.ontology_name == data["ontology_name"]
            ).first()
            if existing:
                continue

            ontology = Ontology(
                organization_id=org.id,
                ontology_db_id=f"onto_{data['ontology_name'].lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
                ontology_name=data["ontology_name"],
                description=data.get("description"),
                authors=data.get("authors"),
                version=data.get("version"),
                licence=data.get("licence"),
                documentation_url=data.get("documentation_url"),
            )
            self.db.add(ontology)
            total += 1

        # Seed Lists
        for data in DEMO_LISTS:
            existing = self.db.query(ListModel).filter(
                ListModel.list_name == data["list_name"]
            ).first()
            if existing:
                continue

            list_obj = ListModel(
                organization_id=org.id,
                list_db_id=f"list_{data['list_name'].lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
                list_name=data["list_name"],
                list_description=data.get("list_description"),
                list_type=data.get("list_type"),
                list_size=data.get("list_size", 0),
                list_owner_name=data.get("list_owner_name"),
                data=data.get("data", []),
            )
            self.db.add(list_obj)
            total += 1

        self.db.commit()
        logger.info(f"Seeded {total} BrAPI Core records")
        return total

    def clear(self) -> int:
        """Clear demo BrAPI Core data"""
        org = self.db.query(Organization).filter(
            Organization.name == "Demo Organization"
        ).first()
        if not org:
            return 0

        total = 0

        # Delete people
        count = self.db.query(Person).filter(
            Person.organization_id == org.id
        ).delete()
        total += count

        # Delete lists
        count = self.db.query(ListModel).filter(
            ListModel.organization_id == org.id
        ).delete()
        total += count

        # Delete ontologies
        count = self.db.query(Ontology).filter(
            Ontology.organization_id == org.id
        ).delete()
        total += count

        # Delete seasons
        count = self.db.query(Season).filter(
            Season.organization_id == org.id
        ).delete()
        total += count

        self.db.commit()
        logger.info(f"Cleared {total} BrAPI Core records")
        return total
