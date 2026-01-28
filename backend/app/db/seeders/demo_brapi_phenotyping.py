"""
Demo BrAPI Phenotyping Reference Data Seeder

Seeds scales, methods, observation levels, traits, and attribute definitions
into the Demo Organization for development and testing.
"""

from sqlalchemy.orm import Session
from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.brapi_phenotyping import (
    Scale, Method, ObservationLevel, Trait,
    GermplasmAttributeDefinition, GermplasmAttributeValue
)
from app.models.germplasm import Germplasm
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


@register_seeder
class DemoBrAPIPhenotypingSeeder(BaseSeeder):
    """Seeds BrAPI phenotyping reference data into Demo Organization"""
    
    name = "demo_brapi_phenotyping"
    priority = 25  # After germplasm seeder
    
    def seed(self) -> int:
        """Seed demo phenotyping reference data"""
        from app.models.core import Organization
        
        count = 0
        
        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        if not demo_org:
            logger.warning("Demo Organization not found, skipping phenotyping seeder")
            return 0
        
        org_id = demo_org.id
        
        # Check if already seeded
        existing = self.db.query(Scale).filter(Scale.organization_id == org_id).first()
        if existing:
            logger.info("BrAPI phenotyping data already seeded")
            return 0
        
        # Seed Scales
        scales_data = [
            {
                "scale_db_id": "scale-001",
                "scale_name": "1-9 Visual Scale",
                "data_type": "Ordinal",
                "decimal_places": 0,
                "valid_values_min": 1,
                "valid_values_max": 9,
                "valid_values_categories": [
                    {"label": "Highly Resistant", "value": "1"},
                    {"label": "Resistant", "value": "3"},
                    {"label": "Moderately Resistant", "value": "5"},
                    {"label": "Susceptible", "value": "7"},
                    {"label": "Highly Susceptible", "value": "9"}
                ],
                "ontology_db_id": "CO_320",
                "ontology_name": "Rice Ontology",
                "ontology_version": "v7"
            },
            {
                "scale_db_id": "scale-002",
                "scale_name": "Centimeters",
                "data_type": "Numerical",
                "decimal_places": 1,
                "valid_values_min": 0,
                "valid_values_max": 500,
                "additional_info": {"unit": "cm"}
            },
            {
                "scale_db_id": "scale-003",
                "scale_name": "Grams",
                "data_type": "Numerical",
                "decimal_places": 2,
                "valid_values_min": 0,
                "valid_values_max": 10000,
                "additional_info": {"unit": "g"}
            },
            {
                "scale_db_id": "scale-004",
                "scale_name": "Percentage",
                "data_type": "Numerical",
                "decimal_places": 1,
                "valid_values_min": 0,
                "valid_values_max": 100,
                "additional_info": {"unit": "%"}
            },
            {
                "scale_db_id": "scale-005",
                "scale_name": "Days",
                "data_type": "Numerical",
                "decimal_places": 0,
                "valid_values_min": 0,
                "valid_values_max": 365,
                "additional_info": {"unit": "days"}
            },
            {
                "scale_db_id": "scale-006",
                "scale_name": "kg/ha",
                "data_type": "Numerical",
                "decimal_places": 0,
                "valid_values_min": 0,
                "valid_values_max": 20000,
                "additional_info": {"unit": "kg/ha"}
            },
            {
                "scale_db_id": "scale-007",
                "scale_name": "Present/Absent",
                "data_type": "Nominal",
                "valid_values_categories": [
                    {"label": "Present", "value": "1"},
                    {"label": "Absent", "value": "0"}
                ]
            }
        ]
        
        for data in scales_data:
            existing = self.db.query(Scale).filter(Scale.scale_db_id == data["scale_db_id"]).first()
            if not existing:
                scale = Scale(organization_id=org_id, **data)
                self.db.add(scale)
                count += 1
        
        # Seed Methods
        methods_data = [
            {
                "method_db_id": "method-001",
                "method_name": "Visual Scoring",
                "method_class": "Estimation",
                "description": "Visual assessment on a 1-9 scale",
                "reference": "IRRI Standard Evaluation System",
                "bibliographical_reference": "IRRI (2013) Standard Evaluation System for Rice",
                "ontology_db_id": "CO_320",
                "ontology_name": "Rice Ontology",
                "ontology_version": "v7"
            },
            {
                "method_db_id": "method-002",
                "method_name": "Ruler Measurement",
                "method_class": "Measurement",
                "description": "Direct measurement using a ruler in centimeters",
                "reference": "Standard measurement protocol"
            },
            {
                "method_db_id": "method-003",
                "method_name": "Electronic Balance",
                "method_class": "Measurement",
                "description": "Weight measurement using electronic balance",
                "reference": "Laboratory protocol"
            },
            {
                "method_db_id": "method-004",
                "method_name": "Grain Counter",
                "method_class": "Counting",
                "description": "Automated grain counting device",
                "reference": "Equipment manual"
            },
            {
                "method_db_id": "method-005",
                "method_name": "Computed",
                "method_class": "Computation",
                "description": "Calculated from other measurements",
                "formula": "yield_kg_ha = (plot_yield_g / plot_area_m2) * 10000 / 1000",
                "reference": "Standard yield calculation"
            }
        ]
        
        for data in methods_data:
            existing = self.db.query(Method).filter(Method.method_db_id == data["method_db_id"]).first()
            if not existing:
                method = Method(organization_id=org_id, **data)
                self.db.add(method)
                count += 1
        
        # Seed Observation Levels
        levels_data = [
            {"level_name": "study", "level_order": 0, "level_code": "STUDY"},
            {"level_name": "field", "level_order": 1, "level_code": "FIELD"},
            {"level_name": "block", "level_order": 2, "level_code": "BLOCK"},
            {"level_name": "rep", "level_order": 3, "level_code": "REP"},
            {"level_name": "plot", "level_order": 4, "level_code": "PLOT"},
            {"level_name": "sub-plot", "level_order": 5, "level_code": "SUBPLOT"},
            {"level_name": "plant", "level_order": 6, "level_code": "PLANT"}
        ]
        
        for data in levels_data:
            existing = self.db.query(ObservationLevel).filter(
                ObservationLevel.organization_id == org_id,
                ObservationLevel.level_name == data["level_name"]
            ).first()
            if not existing:
                level = ObservationLevel(organization_id=org_id, **data)
                self.db.add(level)
                count += 1
        
        # Seed Attribute Definitions
        attrs_data = [
            {
                "attribute_db_id": "attr-001",
                "attribute_name": "Plant Height",
                "attribute_description": "Height of the plant at maturity",
                "attribute_category": "Morphological",
                "data_type": "Numeric",
                "trait_name": "Plant Height",
                "method_name": "Measurement",
                "scale_name": "cm"
            },
            {
                "attribute_db_id": "attr-002",
                "attribute_name": "Days to Flowering",
                "attribute_description": "Number of days from sowing to 50% flowering",
                "attribute_category": "Phenological",
                "data_type": "Numeric",
                "trait_name": "Flowering Time",
                "method_name": "Counting",
                "scale_name": "days"
            },
            {
                "attribute_db_id": "attr-003",
                "attribute_name": "Grain Yield",
                "attribute_description": "Grain yield per hectare",
                "attribute_category": "Agronomic",
                "data_type": "Numeric",
                "trait_name": "Yield",
                "method_name": "Weighing",
                "scale_name": "kg/ha"
            },
            {
                "attribute_db_id": "attr-004",
                "attribute_name": "Disease Resistance",
                "attribute_description": "Resistance to major diseases",
                "attribute_category": "Biotic Stress",
                "data_type": "Ordinal",
                "trait_name": "Disease Resistance",
                "method_name": "Visual Scoring",
                "scale_name": "1-9 scale"
            },
            {
                "attribute_db_id": "attr-005",
                "attribute_name": "Drought Tolerance",
                "attribute_description": "Tolerance to water stress",
                "attribute_category": "Abiotic Stress",
                "data_type": "Ordinal",
                "trait_name": "Drought Tolerance",
                "method_name": "Visual Scoring",
                "scale_name": "1-9 scale"
            },
            {
                "attribute_db_id": "attr-006",
                "attribute_name": "Protein Content",
                "attribute_description": "Protein content in grain",
                "attribute_category": "Quality",
                "data_type": "Numeric",
                "trait_name": "Protein",
                "method_name": "NIR Spectroscopy",
                "scale_name": "%"
            }
        ]
        
        for data in attrs_data:
            existing = self.db.query(GermplasmAttributeDefinition).filter(
                GermplasmAttributeDefinition.attribute_db_id == data["attribute_db_id"]
            ).first()
            if not existing:
                attr_def = GermplasmAttributeDefinition(organization_id=org_id, **data)
                self.db.add(attr_def)
                count += 1
        
        self.db.commit()
        
        # Seed Attribute Values (need germplasm to exist first)
        germplasm_list = self.db.query(Germplasm).filter(
            Germplasm.organization_id == org_id
        ).limit(2).all()
        
        if germplasm_list:
            values_data = [
                {"attribute_db_id": "attr-001", "attribute_name": "Plant Height", "value": "95"},
                {"attribute_db_id": "attr-002", "attribute_name": "Days to Flowering", "value": "85"},
                {"attribute_db_id": "attr-003", "attribute_name": "Grain Yield", "value": "5500"},
                {"attribute_db_id": "attr-004", "attribute_name": "Disease Resistance", "value": "7"},
                {"attribute_db_id": "attr-005", "attribute_name": "Drought Tolerance", "value": "5"},
            ]
            
            for i, germ in enumerate(germplasm_list):
                for j, val_data in enumerate(values_data):
                    av_db_id = f"av-{i+1:03d}-{j+1:03d}"
                    existing = self.db.query(GermplasmAttributeValue).filter(
                        GermplasmAttributeValue.attribute_value_db_id == av_db_id
                    ).first()
                    if not existing:
                        attr_val = GermplasmAttributeValue(
                            organization_id=org_id,
                            germplasm_id=germ.id,
                            attribute_value_db_id=av_db_id,
                            attribute_db_id=val_data["attribute_db_id"],
                            attribute_name=val_data["attribute_name"],
                            germplasm_db_id=germ.germplasm_db_id,
                            germplasm_name=germ.germplasm_name,
                            value=val_data["value"]
                        )
                        self.db.add(attr_val)
                        count += 1
            
            self.db.commit()
        
        logger.info(f"Seeded {count} BrAPI phenotyping reference records")
        return count
    
    def clear(self) -> int:
        """Clear demo phenotyping reference data"""
        from app.models.core import Organization
        
        count = 0
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        if not demo_org:
            return 0
        
        # Delete in reverse order of dependencies
        count += self.db.query(GermplasmAttributeValue).filter(
            GermplasmAttributeValue.organization_id == demo_org.id
        ).delete()
        count += self.db.query(GermplasmAttributeDefinition).filter(
            GermplasmAttributeDefinition.organization_id == demo_org.id
        ).delete()
        count += self.db.query(Trait).filter(
            Trait.organization_id == demo_org.id
        ).delete()
        count += self.db.query(ObservationLevel).filter(
            ObservationLevel.organization_id == demo_org.id
        ).delete()
        count += self.db.query(Method).filter(
            Method.organization_id == demo_org.id
        ).delete()
        count += self.db.query(Scale).filter(
            Scale.organization_id == demo_org.id
        ).delete()
        
        self.db.commit()
        logger.info(f"Cleared {count} BrAPI phenotyping reference records")
        return count
