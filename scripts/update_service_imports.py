#!/usr/bin/env python3
"""
Automated Import Update Script for Service Migration

Updates all imports from flat services/ directory to domain modules.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Mapping of old service imports to new module imports
IMPORT_MAPPINGS = {
    # Genomics domain
    'from app.services.bioinformatics import': 'from app.modules.genomics.services.bioinformatics_service import',
    'from app.services.genomics_data import': 'from app.modules.genomics.services.genomics_data_service import',
    'from app.services.genotyping import': 'from app.modules.genomics.services.genotyping_service import',
    'from app.services.doubled_haploid import': 'from app.modules.genomics.services.doubled_haploid_service import',
    'from app.services.disease_resistance import': 'from app.modules.genomics.services.disease_resistance_service import',
    'from app.services.nirs_prediction import': 'from app.modules.genomics.services.nirs_prediction_service import',
    'from app.services.genetic_diversity import': 'from app.modules.genomics.services.genetic_diversity_service import',
    
    # Breeding domain
    'from app.services.experimental_design_generator import': 'from app.modules.breeding.services.experimental_design_service import',
    'from app.services.genetic_gain import': 'from app.modules.breeding.services.genetic_gain_service import',
    'from app.services.gxe_analysis import': 'from app.modules.breeding.services.gxe_analysis_service import',
    'from app.services.performance_ranking import': 'from app.modules.breeding.services.performance_ranking_service import',
    'from app.services.stability_analysis import': 'from app.modules.breeding.services.stability_analysis_service import',
    'from app.services.variety_licensing import': 'from app.modules.breeding.services.variety_licensing_service import',
    'from app.services.simulation import': 'from app.modules.breeding.services.simulation_service import',
    'from app.services.simulation_service import': 'from app.modules.breeding.services.breeding_simulation_service import',
    'from app.services.proposal_service import': 'from app.modules.breeding.services.proposal_service import',
    'from app.services.performance_service import': 'from app.modules.breeding.services.performance_service import',
    'from app.services.quick_entry import': 'from app.modules.breeding.services.quick_entry_service import',
    'from app.services.yield_gap_service import': 'from app.modules.breeding.services.yield_gap_service import',
    
    # Phenotyping domain
    'from app.services.image_service import': 'from app.modules.phenotyping.services.image_service import',
    'from app.services.observation_search import': 'from app.modules.phenotyping.services.observation_search_service import',
    'from app.services.trait_ontology import': 'from app.modules.phenotyping.services.trait_ontology_service import',
    'from app.services.trait_search import': 'from app.modules.phenotyping.services.trait_search_service import',
    
    # Germplasm domain
    'from app.services.barcode_service import': 'from app.modules.germplasm.services.barcode_service import',
    'from app.services.seed_inventory import': 'from app.modules.germplasm.services.seed_inventory_service import',
    'from app.services.seed_traceability import': 'from app.modules.germplasm.services.seed_traceability_service import',
    'from app.services.seedlot_search import': 'from app.modules.germplasm.services.seedlot_search_service import',
    'from app.services.program_search import': 'from app.modules.germplasm.services.program_search_service import',
    
    # Environment domain
    'from app.services.abiotic_stress import': 'from app.modules.environment.services.abiotic_stress_service import',
    'from app.services.carbon_monitoring_service import': 'from app.modules.environment.services.carbon_monitoring_service import',
    'from app.services.harvest_management import': 'from app.modules.environment.services.harvest_management_service import',
    'from app.services.water_balance_service import': 'from app.modules.environment.services.water_balance_service import',
    'from app.services.emissions_calculator_service import': 'from app.modules.environment.services.emissions_calculator_service import',
    'from app.services.sustainability_metrics_service import': 'from app.modules.environment.services.sustainability_metrics_service import',
    'from app.services.sensor_network import': 'from app.modules.environment.services.sensor_network_service import',
    'from app.services.iot_aggregation import': 'from app.modules.environment.services.iot_aggregation_service import',
    'from app.services.field_gdd_service import': 'from app.modules.environment.services.field_gdd_service import',
    'from app.services.cross_domain_gdd_service import': 'from app.modules.environment.services.cross_domain_gdd_service import',
    'from app.services.gdd_error_handler import': 'from app.modules.environment.services.gdd_error_handler_service import',
    'from app.services.solar import': 'from app.modules.environment.services.solar_service import',
    'from app.services.space_research import': 'from app.modules.environment.services.space_research_service import',
    'from app.services.crop_calendar import': 'from app.modules.environment.services.crop_calendar_service import',
    
    # Spatial domain
    'from app.services.soil_analysis import': 'from app.modules.spatial.services.soil_analysis_service import',
    'from app.services.spatial import': 'from app.modules.spatial.services.spatial_service import',
    'from app.services.field_layout_service import': 'from app.modules.spatial.services.field_layout_service import',
    
    # AI domain
    'from app.services.biosimulation import': 'from app.modules.ai.services.biosimulation_service import',
    'from app.services.correlation_analysis import': 'from app.modules.ai.services.correlation_analysis_service import',
    'from app.services.dimensionality_reduction import': 'from app.modules.ai.services.dimensionality_reduction_service import',
    'from app.services.mixed_model import': 'from app.modules.ai.services.mixed_model_service import',
    'from app.services.statistics_calculator import': 'from app.modules.ai.services.statistics_calculator_service import',
    'from app.services.devguru_service import': 'from app.modules.ai.services.devguru_service import',
    'from app.services.ml_bounding_box_extractor import': 'from app.modules.ai.services.ml_bounding_box_extractor_service import',
    'from app.services.statistics import': 'from app.modules.ai.services.statistics_service import',
    'from app.services.reevu_provenance_validator import': 'from app.modules.ai.services.reevu_provenance_validator import',
    
    # Core domain
    'from app.services.collaboration_service import': 'from app.modules.core.services.collaboration_service import',
    'from app.services.data_export import': 'from app.modules.core.services.data_export_service import',
    'from app.services.data_quality_service import': 'from app.modules.core.services.data_quality_service import',
    'from app.services.data_quality import': 'from app.modules.core.services.data_quality import',
    'from app.services.processing_batch import': 'from app.modules.core.services.processing_batch_service import',
    'from app.services.quality_control import': 'from app.modules.core.services.quality_control_service import',
    'from app.services.security_audit import': 'from app.modules.core.services.security_audit_service import',
    'from app.services.redis_security import': 'from app.modules.core.services.redis_security_service import',
    'from app.services.label_printing import': 'from app.modules.core.services.label_printing_service import',
    'from app.services.scales_service import': 'from app.modules.core.services.scales_service import',
    'from app.services.dispatch_management import': 'from app.modules.core.services.dispatch_management_service import',
    'from app.services.progress_tracker import': 'from app.modules.core.services.progress_tracker_service import',
    'from app.services.voice_service import': 'from app.modules.core.services.voice_service import',
    'from app.services.vault_sensors import': 'from app.modules.core.services.vault_sensors_service import',
    'from app.services.math_utils import': 'from app.modules.core.services.math_utils_service import',
    
    # Interop domain
    'from app.services.dus_testing import': 'from app.modules.interop.services.dus_testing_service import',
    'from app.services.dus_crops import': 'from app.modules.interop.services.dus_crops_service import',
    'from app.services.economics import': 'from app.modules.interop.services.economics_service import',
    
    # Subdirectories
    'from app.services.analytics': 'from app.modules.genomics.compute.analytics',
    'from app.services.reevu': 'from app.modules.ai.services.reevu',
    'from app.services.chaitanya': 'from app.modules.ai.services.chaitanya',
    'from app.services.infra': 'from app.modules.core.services.infra',
    'from app.services.compliance': 'from app.modules.core.services.compliance',
    'from app.services.import_engine': 'from app.modules.core.services.import_engine',
    'from app.services.ledger': 'from app.modules.core.services.ledger',
    'from app.services.prahari': 'from app.modules.core.services.prahari',
    'from app.services.rakshaka': 'from app.modules.core.services.rakshaka',
    'from app.services.social': 'from app.modules.core.services.social',
    'from app.services.robotics': 'from app.modules.spatial.services.robotics',
    'from app.services.iot': 'from app.modules.environment.services.iot',
    'from app.services.core': 'from app.modules.core.services.seasons',
}


def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the backend directory."""
    root = Path(root_dir)
    return list(root.rglob("*.py"))


def update_imports_in_file(file_path: Path, mappings: Dict[str, str]) -> Tuple[int, List[str]]:
    """
    Update imports in a single file.
    
    Returns:
        Tuple of (number of replacements, list of changes made)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []
    
    original_content = content
    replacements = 0
    changes = []
    
    # Apply each mapping
    for old_import, new_import in mappings.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            count = original_content.count(old_import)
            replacements += count
            changes.append(f"  {old_import} -> {new_import} ({count}x)")
    
    # Write back if changes were made
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return replacements, changes
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0, []
    
    return 0, []


def main():
    """Main execution function."""
    print("=" * 80)
    print("Service Import Update Script")
    print("=" * 80)
    print()
    
    # Find all Python files
    backend_dir = Path(__file__).parent.parent / "backend" / "app"
    print(f"Scanning directory: {backend_dir}")
    
    python_files = find_python_files(str(backend_dir))
    print(f"Found {len(python_files)} Python files")
    print()
    
    # Update imports in each file
    total_replacements = 0
    files_modified = 0
    
    for file_path in python_files:
        replacements, changes = update_imports_in_file(file_path, IMPORT_MAPPINGS)
        
        if replacements > 0:
            files_modified += 1
            total_replacements += replacements
            print(f"✓ {file_path.relative_to(backend_dir.parent)}")
            for change in changes:
                print(change)
            print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files scanned: {len(python_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Total replacements: {total_replacements}")
    print()
    
    if files_modified > 0:
        print("✓ Import updates complete!")
        print()
        print("Next steps:")
        print("1. Run tests: pytest backend/tests")
        print("2. Check for any remaining old imports:")
        print("   grep -r 'from app.services' backend/app --include='*.py'")
        print("3. Commit changes: git add . && git commit -m 'refactor: update service imports to domain modules'")
    else:
        print("No imports needed updating.")


if __name__ == "__main__":
    main()
