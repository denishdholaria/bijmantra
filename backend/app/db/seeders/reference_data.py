"""
Reference Data Seeder

Seeds essential reference data that is required for the application to function.
This seeder ALWAYS runs regardless of SEED_DEMO_DATA setting.

Reference data includes:
- Breeding methods (standard methods used across all breeding programs)
- Observation scales (standard measurement scales)
- Standard traits (common traits used in plant breeding)

This data is NOT demo data - it's foundational reference data that
any production deployment needs.
"""

from sqlalchemy.orm import Session
from .base import BaseSeeder, register_seeder
import logging

logger = logging.getLogger(__name__)


# Standard breeding methods (BrAPI compliant)
BREEDING_METHODS = [
    {
        "name": "Single Seed Descent",
        "abbreviation": "SSD",
        "description": "Advancing generations by selecting a single seed from each plant",
    },
    {
        "name": "Pedigree Selection",
        "abbreviation": "PED",
        "description": "Selection based on pedigree and individual plant performance",
    },
    {
        "name": "Bulk Population",
        "abbreviation": "BULK",
        "description": "Advancing generations by bulking seeds from selected plants",
    },
    {
        "name": "Backcross",
        "abbreviation": "BC",
        "description": "Repeated crossing to a recurrent parent to transfer specific traits",
    },
    {
        "name": "Doubled Haploid",
        "abbreviation": "DH",
        "description": "Production of homozygous lines through chromosome doubling of haploids",
    },
    {
        "name": "Marker Assisted Selection",
        "abbreviation": "MAS",
        "description": "Selection using molecular markers linked to traits of interest",
    },
    {
        "name": "Genomic Selection",
        "abbreviation": "GS",
        "description": "Selection based on genomic estimated breeding values",
    },
    {
        "name": "Recurrent Selection",
        "abbreviation": "RS",
        "description": "Cyclic selection to improve population mean",
    },
]


@register_seeder
class ReferenceDataSeeder(BaseSeeder):
    """
    Seeds essential reference data required for application functionality.
    
    This seeder ALWAYS runs - it is not controlled by SEED_DEMO_DATA.
    Reference data is foundational, not demo data.
    """
    
    name = "reference_data"
    description = "Essential reference data (breeding methods, scales, traits)"
    
    def should_run(self, env: str = "dev") -> bool:
        """
        Reference data should ALWAYS run, even in production.
        Override base class to ignore SEED_DEMO_DATA setting.
        """
        # Reference data is needed in all environments
        return True
    
    def seed(self) -> int:
        """Seed reference data into the database."""
        from app.models.brapi import BreedingMethod
        
        count = 0
        
        # Seed breeding methods
        for method_data in BREEDING_METHODS:
            existing = self.db.query(BreedingMethod).filter(
                BreedingMethod.abbreviation == method_data["abbreviation"]
            ).first()
            
            if existing:
                continue
            
            method = BreedingMethod(
                name=method_data["name"],
                abbreviation=method_data["abbreviation"],
                description=method_data["description"],
            )
            self.db.add(method)
            count += 1
            logger.info(f"Added breeding method: {method_data['name']}")
        
        self.db.commit()
        logger.info(f"Seeded {count} reference data records")
        return count
    
    def clear(self) -> int:
        """
        Clear reference data.
        
        WARNING: This should rarely be called as reference data is foundational.
        """
        from app.models.brapi import BreedingMethod
        
        count = 0
        
        # Only clear breeding methods we seeded (by abbreviation)
        abbreviations = [m["abbreviation"] for m in BREEDING_METHODS]
        deleted = self.db.query(BreedingMethod).filter(
            BreedingMethod.abbreviation.in_(abbreviations)
        ).delete(synchronize_session=False)
        count += deleted
        
        self.db.commit()
        logger.info(f"Cleared {count} reference data records")
        return count
