#!/usr/bin/env python3
"""
Check Service Migration Progress

This script checks that no new services are added to the flat services/ directory
and tracks migration progress.

Usage:
    python scripts/check_service_migration.py
"""

import sys
from pathlib import Path
from typing import Set, List

try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is required for this script")
    print("   Install it with: pip install PyYAML")
    sys.exit(1)


# Allowed legacy services (existing services during migration)
# These are allowed to remain in services/ temporarily
ALLOWED_LEGACY_SERVICES = {
    # Core infrastructure (will remain in services/)
    "task_queue.py",
    "compute_engine.py",
    "event_bus.py",
    
    # Services to be migrated in Phase 2-5
    "authorization.py",
    "job_service.py",
    
    # Breeding domain services
    "breeding_value.py",
    "breeding_pipeline.py",
    "cross_service.py",
    "cross_prediction.py",
    "crossing_planner.py",
    
    # Genomics domain services
    "gwas.py",
    "genomic_selection.py",
    "marker_assisted.py",
    "molecular_breeding.py",
    "population_genetics.py",
    "qtl_mapping.py",
    "haplotype_analysis.py",
    "ld_analysis.py",
    "snp_clustering.py",
    "parentage_analysis.py",
    
    # Phenotyping domain services
    "phenotype_analysis.py",
    "phenomic_selection.py",
    "phenology.py",
    "image_analysis.py",
    
    # Environment domain services
    "weather_service.py",
    "weather_integration.py",
    "field_environment.py",
    "gdd_calculator_service.py",
    "gee_integration_service.py",
    "environmental_physics.py",
    
    # Spatial domain services
    "spatial_analysis.py",
    "spatial_correction.py",
    "maps_service.py",
    "location_search.py",
    
    # AI domain services
    "veena_service.py",
    "veena_cognitive_service.py",
    "function_calling_service.py",
    
    # Interop domain services
    "integration_hub.py",
    "grin_global.py",
}

# Allowed legacy subdirectories
ALLOWED_LEGACY_SUBDIRS = {
    "ai",
    "analytics",
    "compliance",
    "genomics_statistics",
    "iot",
    "phenotyping",
    "robotics",
    "infra",
}


def get_services_in_flat_directory(services_dir: Path) -> Set[str]:
    """Get all service files in the flat services directory."""
    if not services_dir.exists():
        return set()
    
    services = set()
    
    # Get top-level service files
    for service_file in services_dir.glob("*.py"):
        if service_file.name == "__init__.py":
            continue
        services.add(service_file.name)
    
    # Get services in subdirectories
    for subdir in services_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("_"):
            for service_file in subdir.rglob("*.py"):
                if service_file.name == "__init__.py":
                    continue
                rel_path = service_file.relative_to(services_dir)
                services.add(str(rel_path))
    
    return services


def get_migration_progress(registry_path: Path) -> dict:
    """Get migration progress from domain registry."""
    if not registry_path.exists():
        return {"total": 0, "migrated": 0, "domains": {}}
    
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)
    
    total_services = 0
    migrated_services = 0
    domain_progress = {}
    
    for domain, config in registry.items():
        if isinstance(config, dict) and "services" in config:
            domain_services = len(config["services"])
            total_services += domain_services
            
            # Check if services are actually migrated (exist in modules)
            modules_dir = registry_path.parent / "modules" / domain
            if modules_dir.exists():
                migrated_count = 0
                service_file = modules_dir / "service.py"
                services_dir = modules_dir / "services"
                
                if service_file.exists():
                    migrated_count += 1
                if services_dir.exists():
                    migrated_count += len(list(services_dir.rglob("*.py"))) - len(list(services_dir.rglob("__init__.py")))
                
                migrated_services += migrated_count
                domain_progress[domain] = {
                    "total": domain_services,
                    "migrated": migrated_count
                }
    
    return {
        "total": total_services,
        "migrated": migrated_services,
        "domains": domain_progress
    }


def check_new_services(current_services: Set[str]) -> List[str]:
    """Check for new services that violate the migration policy."""
    violations = []
    
    for service in current_services:
        # Check if it's a top-level service file
        if "/" not in service:
            if service not in ALLOWED_LEGACY_SERVICES:
                violations.append(f"New service in flat directory: {service}")
        else:
            # Check if it's in an allowed subdirectory
            subdir = service.split("/")[0]
            if subdir not in ALLOWED_LEGACY_SUBDIRS:
                violations.append(f"New service in unauthorized subdirectory: {service}")
    
    return violations


def main():
    """Main validation function."""
    print("🔍 Checking Service Migration Progress...")
    print()
    
    # Paths
    backend_dir = Path(__file__).parent.parent
    services_dir = backend_dir / "app" / "services"
    registry_path = backend_dir / "app" / "domain_registry.yaml"
    
    # Get current services
    current_services = get_services_in_flat_directory(services_dir)
    
    print(f"📊 Current State:")
    print(f"   Services in flat directory: {len(current_services)}")
    print()
    
    # Check for new services
    print("🔍 Checking for policy violations...")
    violations = check_new_services(current_services)
    
    if violations:
        print("❌ Architecture policy violations detected:")
        print()
        print("   New services MUST be created in domain modules, not in services/")
        print("   Location: backend/app/modules/{domain}/services/")
        print()
        for violation in violations:
            print(f"   ❌ {violation}")
        print()
        sys.exit(1)
    
    print("✅ No new services in flat directory (policy compliant)")
    print()
    
    # Get migration progress
    print("📈 Migration Progress:")
    progress = get_migration_progress(registry_path)
    
    if progress["total"] > 0:
        percentage = (progress["migrated"] / progress["total"]) * 100
        print(f"   Overall: {progress['migrated']}/{progress['total']} services migrated ({percentage:.1f}%)")
        print()
        
        if progress["domains"]:
            print("   By Domain:")
            for domain, stats in progress["domains"].items():
                domain_pct = (stats["migrated"] / stats["total"] * 100) if stats["total"] > 0 else 0
                status = "✅" if stats["migrated"] == stats["total"] else "🔄"
                print(f"   {status} {domain}: {stats['migrated']}/{stats['total']} ({domain_pct:.0f}%)")
    else:
        print("   Migration tracking not yet available")
    
    print()
    print("✨ Service migration check complete!")


if __name__ == "__main__":
    main()
