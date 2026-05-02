#!/usr/bin/env python3
"""Fix test imports after service migration"""

import os
import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Analytics (moved to genomics/compute)
    "from app.services.analytics": "from app.modules.genomics.compute.analytics",
    
    # Genomics services
    "from app.services.bioinformatics": "from app.modules.genomics.services.bioinformatics_service",
    "from app.services.genetic_diversity": "from app.modules.genomics.services.genetic_diversity_service",
    "from app.services.nirs_prediction": "from app.modules.genomics.services.nirs_prediction_service",
    
    # Breeding services
    "from app.services.experimental_design_generator": "from app.modules.breeding.services.experimental_design_service",
    "from app.services.gxe_analysis": "from app.modules.breeding.services.gxe_analysis_service",
    "from app.services.simulation": "from app.modules.breeding.services.simulation_service",
    "from app.services.yield_gap_service": "from app.modules.breeding.services.yield_gap_service",
    
    # Germplasm services
    "from app.services.barcode_service": "from app.modules.germplasm.services.barcode_service",
    
    # Environment services
    "from app.services.carbon_monitoring_service": "from app.modules.environment.services.carbon_monitoring_service",
    "from app.services.emissions_calculator_service": "from app.modules.environment.services.emissions_calculator_service",
    "from app.services.weather_integration_service": "from app.modules.environment.services.weather_integration_service",
    "from backend.app.services.cross_domain_gdd_service": "from app.modules.environment.services.cross_domain_gdd_service",
    "from backend.app.services.environmental_physics": "from app.modules.environment.services.environmental_physics_service",
    "from backend.app.services.solar": "from app.modules.environment.services.solar_service",
    
    # AI services
    "from app.services.biosimulation": "from app.modules.ai.services.biosimulation_service",
    "from app.services.dimensionality_reduction": "from app.modules.ai.services.dimensionality_reduction_service",
    "from app.services.mixed_model": "from app.modules.ai.services.mixed_model_service",
    "from app.services.statistics_calculator": "from app.modules.ai.services.statistics_calculator_service",
    "from app.services.reevu": "from app.modules.ai.services.reevu",
    "from app.services.llm_service": "from app.modules.ai.services.llm_service",
    "from app.services.ml_bounding_box_extractor": "from app.modules.ai.services.ml_bounding_box_extractor",
    
    # Core services
    "from app.services.compliance": "from app.modules.core.services.compliance",
    "from app.services.infra": "from app.modules.core.services.infra",
    "from backend.app.services.infra": "from app.modules.core.services.infra",
    "from app.services.label_printing": "from app.modules.core.services.label_printing_service",
    "from app.services.progress_tracker": "from app.modules.core.services.progress_tracker_service",
    "from backend.app.services.data_quality_service": "from app.modules.core.services.data_quality_service",
    "from backend.app.services.math_utils": "from app.modules.core.services.math_utils_service",
    "from backend.app.services.vision_annotation": "from app.modules.phenotyping.services.vision_annotation",
    
    # Remove backend. prefix
    "from backend.tests": "from tests",
}

def fix_file(filepath):
    """Fix imports in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Apply all mappings
    for old_import, new_import in IMPORT_MAPPINGS.items():
        content = content.replace(old_import, new_import)
    
    # Write back if changed
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all test files"""
    test_dir = Path("backend/tests")
    fixed_count = 0
    
    for filepath in test_dir.rglob("*.py"):
        if fix_file(filepath):
            print(f"Fixed: {filepath}")
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} test files")

if __name__ == "__main__":
    main()
