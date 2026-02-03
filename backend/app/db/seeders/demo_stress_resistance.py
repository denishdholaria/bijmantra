"""
Demo Stress Resistance Seeder
Seeds abiotic stress and disease resistance data for Demo Organization
"""
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.core import Organization
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_seeder
class DemoStressResistanceSeeder(BaseSeeder):
    """Seeds abiotic stress and disease resistance demo data"""
    
    name = "demo_stress_resistance"
    priority = 60  # After core data
    
    def seed(self) -> int:
        """Seed stress resistance data"""
        from app.models.stress_resistance import (
            AbioticStress, ToleranceGene, Disease, ResistanceGene, PyramidingStrategy,
            StressCategory, PathogenType, ResistanceType
        )
        
        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            logger.warning("Demo Organization not found, skipping stress resistance seeding")
            return 0
        
        count = 0
        org_id = demo_org.id
        
        # Check if already seeded
        existing = self.db.query(AbioticStress).filter(
            AbioticStress.organization_id == org_id
        ).first()
        if existing:
            logger.info("Stress resistance data already seeded")
            return 0
        
        # ============================================
        # ABIOTIC STRESSES
        # ============================================
        stresses_data = [
            {
                "stress_code": "STR-001",
                "name": "Drought",
                "category": StressCategory.WATER,
                "description": "Water deficit stress affecting plant growth and yield",
                "screening_method": "Managed Stress Environment",
                "screening_stages": ["Vegetative", "Reproductive"],
                "screening_duration": "14-21 days",
                "indicators": ["Leaf rolling", "Canopy temperature", "NDVI"],
            },
            {
                "stress_code": "STR-002",
                "name": "Heat",
                "category": StressCategory.TEMPERATURE,
                "description": "High temperature stress affecting flowering and grain filling",
                "screening_method": "Growth chamber/Field",
                "screening_stages": ["Flowering"],
                "screening_duration": "5-7 days",
                "indicators": ["Spikelet fertility", "Pollen viability"],
            },
            {
                "stress_code": "STR-003",
                "name": "Cold",
                "category": StressCategory.TEMPERATURE,
                "description": "Low temperature/chilling stress affecting seedling vigor",
                "screening_method": "Cold chamber",
                "screening_stages": ["Seedling", "Booting"],
                "screening_duration": "7-14 days",
                "indicators": ["Seedling survival", "Chlorosis"],
            },
            {
                "stress_code": "STR-004",
                "name": "Salinity",
                "category": StressCategory.SOIL,
                "description": "Salt stress in soil affecting ion balance",
                "screening_method": "Hydroponics/Pot culture",
                "screening_stages": ["Seedling", "Vegetative"],
                "screening_duration": "14 days",
                "indicators": ["Na+/K+ ratio", "Chlorophyll content", "Biomass"],
            },
            {
                "stress_code": "STR-005",
                "name": "Submergence",
                "category": StressCategory.WATER,
                "description": "Flooding/waterlogging stress",
                "screening_method": "Tank submergence",
                "screening_stages": ["Vegetative"],
                "screening_duration": "14-17 days",
                "indicators": ["Survival rate", "Elongation", "Recovery"],
            },
            {
                "stress_code": "STR-006",
                "name": "Nutrient Deficiency",
                "category": StressCategory.NUTRIENT,
                "description": "Low nutrient availability affecting growth",
                "screening_method": "Hydroponics",
                "screening_stages": ["Vegetative"],
                "screening_duration": "21 days",
                "indicators": ["Chlorosis", "Biomass", "Root architecture"],
            },
            {
                "stress_code": "STR-007",
                "name": "Heavy Metal",
                "category": StressCategory.SOIL,
                "description": "Toxic metal accumulation in soil",
                "screening_method": "Pot culture",
                "screening_stages": ["Seedling", "Vegetative"],
                "screening_duration": "14-21 days",
                "indicators": ["Metal uptake", "Biomass", "Chlorosis"],
            },
            {
                "stress_code": "STR-008",
                "name": "UV Radiation",
                "category": StressCategory.RADIATION,
                "description": "High UV exposure affecting photosynthesis",
                "screening_method": "UV chamber",
                "screening_stages": ["Vegetative"],
                "screening_duration": "7 days",
                "indicators": ["Leaf damage", "Chlorophyll fluorescence"],
            },
        ]
        
        stress_map = {}  # Map stress_code to id for gene linking
        for data in stresses_data:
            stress = AbioticStress(
                organization_id=org_id,
                **data
            )
            self.db.add(stress)
            self.db.flush()  # Get the auto-generated ID
            stress_map[data["stress_code"]] = stress.id
            count += 1
        
        # ============================================
        # TOLERANCE GENES
        # ============================================
        tolerance_genes_data = [
            {"gene_code": "TGENE-001", "name": "DREB1A", "stress_code": "STR-001", "mechanism": "transcription factor", "crop": "Multiple", "markers": []},
            {"gene_code": "TGENE-002", "name": "LEA proteins", "stress_code": "STR-001", "mechanism": "osmoprotection", "crop": "Multiple", "markers": []},
            {"gene_code": "TGENE-003", "name": "HSP101", "stress_code": "STR-002", "mechanism": "protein folding", "crop": "Multiple", "markers": []},
            {"gene_code": "TGENE-004", "name": "Sub1A", "stress_code": "STR-005", "mechanism": "ethylene response", "crop": "Rice", "chromosome": "9", "markers": ["Sub1-SSR", "Sub1-CAPS"]},
            {"gene_code": "TGENE-005", "name": "Saltol", "stress_code": "STR-004", "mechanism": "ion exclusion", "crop": "Rice", "chromosome": "1", "markers": ["RM3412", "RM493"]},
            {"gene_code": "TGENE-006", "name": "SKC1", "stress_code": "STR-004", "mechanism": "K+/Na+ homeostasis", "crop": "Rice", "chromosome": "1", "markers": ["SKC1-STS"]},
            {"gene_code": "TGENE-007", "name": "qDTY1.1", "stress_code": "STR-001", "mechanism": "grain yield under drought", "crop": "Rice", "chromosome": "1", "markers": ["RM431", "RM12091"]},
            {"gene_code": "TGENE-008", "name": "SNAC1", "stress_code": "STR-001", "mechanism": "stomatal closure", "crop": "Rice", "chromosome": "9", "markers": []},
            {"gene_code": "TGENE-009", "name": "OsNAC9", "stress_code": "STR-001", "mechanism": "root development", "crop": "Rice", "chromosome": "6", "markers": []},
            {"gene_code": "TGENE-010", "name": "CBF/DREB1", "stress_code": "STR-003", "mechanism": "cold acclimation", "crop": "Multiple", "markers": []},
        ]
        
        for data in tolerance_genes_data:
            stress_code = data.pop("stress_code")
            gene = ToleranceGene(
                organization_id=org_id,
                stress_id=stress_map[stress_code],
                is_validated=len(data.get("markers", [])) > 0,
                **data
            )
            self.db.add(gene)
            count += 1
        
        # ============================================
        # DISEASES
        # ============================================
        diseases_data = [
            {"disease_code": "DIS-001", "name": "Bacterial Blight", "pathogen": "Xanthomonas oryzae pv. oryzae", "pathogen_type": PathogenType.BACTERIA, "crop": "Rice", "symptoms": "Water-soaked lesions, wilting", "severity_scale": ["0", "1", "3", "5", "7", "9"]},
            {"disease_code": "DIS-002", "name": "Blast", "pathogen": "Magnaporthe oryzae", "pathogen_type": PathogenType.FUNGUS, "crop": "Rice", "symptoms": "Diamond-shaped lesions", "severity_scale": ["0", "1", "3", "5", "7", "9"]},
            {"disease_code": "DIS-003", "name": "Brown Planthopper", "pathogen": "Nilaparvata lugens", "pathogen_type": PathogenType.INSECT, "crop": "Rice", "symptoms": "Hopper burn, stunting", "severity_scale": ["0", "1", "3", "5", "7", "9"]},
            {"disease_code": "DIS-004", "name": "Stem Rust", "pathogen": "Puccinia graminis", "pathogen_type": PathogenType.FUNGUS, "crop": "Wheat", "symptoms": "Reddish-brown pustules on stems", "severity_scale": ["0", "5", "10", "20", "40", "60", "100"]},
            {"disease_code": "DIS-005", "name": "Yellow Rust", "pathogen": "Puccinia striiformis", "pathogen_type": PathogenType.FUNGUS, "crop": "Wheat", "symptoms": "Yellow stripes on leaves", "severity_scale": ["0", "5", "10", "20", "40", "60", "100"]},
            {"disease_code": "DIS-006", "name": "Northern Corn Leaf Blight", "pathogen": "Exserohilum turcicum", "pathogen_type": PathogenType.FUNGUS, "crop": "Maize", "symptoms": "Cigar-shaped lesions", "severity_scale": ["1", "2", "3", "4", "5"]},
            {"disease_code": "DIS-007", "name": "Gray Leaf Spot", "pathogen": "Cercospora zeae-maydis", "pathogen_type": PathogenType.FUNGUS, "crop": "Maize", "symptoms": "Rectangular gray lesions", "severity_scale": ["1", "2", "3", "4", "5"]},
            {"disease_code": "DIS-008", "name": "Sheath Blight", "pathogen": "Rhizoctonia solani", "pathogen_type": PathogenType.FUNGUS, "crop": "Rice", "symptoms": "Oval lesions on sheath", "severity_scale": ["0", "1", "3", "5", "7", "9"]},
        ]
        
        disease_map = {}  # Map disease_code to id for gene linking
        for data in diseases_data:
            disease = Disease(
                organization_id=org_id,
                **data
            )
            self.db.add(disease)
            self.db.flush()  # Get the auto-generated ID
            disease_map[data["disease_code"]] = disease.id
            count += 1
        
        # ============================================
        # RESISTANCE GENES
        # ============================================
        resistance_genes_data = [
            {"gene_code": "RGENE-001", "name": "Xa21", "disease_code": "DIS-001", "chromosome": "11", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "O. longistaminata", "markers": ["pTA248", "Xa21-STS"]},
            {"gene_code": "RGENE-002", "name": "xa13", "disease_code": "DIS-001", "chromosome": "8", "resistance_type": ResistanceType.RECESSIVE, "source_germplasm": "BJ1", "markers": ["xa13-prom"]},
            {"gene_code": "RGENE-003", "name": "xa5", "disease_code": "DIS-001", "chromosome": "5", "resistance_type": ResistanceType.RECESSIVE, "source_germplasm": "DZ192", "markers": ["RM122", "xa5-1"]},
            {"gene_code": "RGENE-004", "name": "Pi-ta", "disease_code": "DIS-002", "chromosome": "12", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "Tetep", "markers": ["YL155/YL87"]},
            {"gene_code": "RGENE-005", "name": "Pi9", "disease_code": "DIS-002", "chromosome": "6", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "O. minuta", "markers": ["Pi9-STS"]},
            {"gene_code": "RGENE-006", "name": "Bph3", "disease_code": "DIS-003", "chromosome": "6", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "Rathu Heenati", "markers": ["RM589", "RM586"]},
            {"gene_code": "RGENE-007", "name": "Sr31", "disease_code": "DIS-004", "chromosome": "1BL/1RS", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "Petkus rye", "markers": ["iag95"]},
            {"gene_code": "RGENE-008", "name": "Yr15", "disease_code": "DIS-005", "chromosome": "1BS", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "T. dicoccoides", "markers": ["Xbarc8"]},
            {"gene_code": "RGENE-009", "name": "Ht1", "disease_code": "DIS-006", "chromosome": "2", "resistance_type": ResistanceType.PARTIAL, "source_germplasm": "Ladyfinger popcorn", "markers": ["umc1065"]},
            {"gene_code": "RGENE-010", "name": "Pi2", "disease_code": "DIS-002", "chromosome": "6", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "5173", "markers": ["AP22", "AP5659-5"]},
            {"gene_code": "RGENE-011", "name": "Xa4", "disease_code": "DIS-001", "chromosome": "11", "resistance_type": ResistanceType.COMPLETE, "source_germplasm": "TKM6", "markers": ["MP1", "MP2"]},
        ]
        
        for data in resistance_genes_data:
            disease_code = data.pop("disease_code")
            gene = ResistanceGene(
                organization_id=org_id,
                disease_id=disease_map[disease_code],
                is_validated=len(data.get("markers", [])) > 0,
                **data
            )
            self.db.add(gene)
            count += 1
        
        # ============================================
        # PYRAMIDING STRATEGIES
        # ============================================
        strategies_data = [
            {
                "strategy_code": "PYR-001",
                "name": "Bacterial Blight Pyramid",
                "target_disease": "Bacterial Blight",
                "gene_names": ["Xa21", "xa13", "xa5"],
                "description": "Combine Xa21 + xa13 + xa5 for broad-spectrum resistance",
                "status": "recommended",
            },
            {
                "strategy_code": "PYR-002",
                "name": "Blast Resistance Pyramid",
                "target_disease": "Blast",
                "gene_names": ["Pi-ta", "Pi9", "Pi2"],
                "description": "Stack Pi-ta + Pi9 + Pi2 for multiple race resistance",
                "status": "recommended",
            },
            {
                "strategy_code": "PYR-003",
                "name": "Rust Resistance (Wheat)",
                "target_disease": "Stem Rust",
                "gene_names": ["Sr31", "Sr38", "Sr2"],
                "description": "Sr31 breakdown reported - consider adding Sr38 or Sr2",
                "status": "warning",
                "warning_message": "Sr31 breakdown reported in Ug99 race",
            },
            {
                "strategy_code": "PYR-004",
                "name": "Drought + Submergence",
                "target_stress": "Multiple",
                "gene_names": ["qDTY1.1", "Sub1A"],
                "description": "Combine drought and submergence tolerance for climate resilience",
                "status": "recommended",
            },
        ]
        
        for data in strategies_data:
            strategy = PyramidingStrategy(
                organization_id=org_id,
                **data
            )
            self.db.add(strategy)
            count += 1
        
        self.db.commit()
        logger.info(f"Seeded {count} stress resistance records")
        return count
    
    def clear(self) -> int:
        """Clear stress resistance data"""
        from app.models.stress_resistance import (
            AbioticStress, ToleranceGene, Disease, ResistanceGene, PyramidingStrategy
        )
        
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        
        if not demo_org:
            return 0
        
        count = 0
        
        # Delete in order (children first)
        count += self.db.query(ToleranceGene).filter(
            ToleranceGene.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(AbioticStress).filter(
            AbioticStress.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(ResistanceGene).filter(
            ResistanceGene.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(Disease).filter(
            Disease.organization_id == demo_org.id
        ).delete()
        
        count += self.db.query(PyramidingStrategy).filter(
            PyramidingStrategy.organization_id == demo_org.id
        ).delete()
        
        self.db.commit()
        return count
