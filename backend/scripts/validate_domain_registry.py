#!/usr/bin/env python3
"""
Validate Domain Registry

This script validates that the domain_registry.yaml file is properly structured
and that all services are registered to a domain.

Usage:
    python scripts/validate_domain_registry.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is required for this script")
    print("   Install it with: pip install PyYAML")
    sys.exit(1)


def load_domain_registry(registry_path: Path) -> Dict:
    """Load the domain registry YAML file."""
    if not registry_path.exists():
        print(f"❌ Error: Domain registry not found at {registry_path}")
        sys.exit(1)
    
    with open(registry_path, 'r') as f:
        return yaml.safe_load(f)


def get_services_in_directory(services_dir: Path) -> Set[str]:
    """Get all service files in the services directory."""
    if not services_dir.exists():
        return set()
    
    services = set()
    for service_file in services_dir.rglob("*.py"):
        if service_file.name == "__init__.py":
            continue
        # Get relative path from services directory
        rel_path = service_file.relative_to(services_dir)
        services.add(str(rel_path))
    
    return services


def get_services_in_modules(modules_dir: Path) -> Dict[str, List[str]]:
    """Get all service files organized by domain module."""
    if not modules_dir.exists():
        return {}
    
    domain_services = {}
    for domain_dir in modules_dir.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        
        services = []
        service_file = domain_dir / "service.py"
        if service_file.exists():
            services.append("service.py")
        
        services_dir = domain_dir / "services"
        if services_dir.exists():
            for service_file in services_dir.rglob("*.py"):
                if service_file.name == "__init__.py":
                    continue
                rel_path = service_file.relative_to(services_dir)
                services.append(f"services/{rel_path}")
        
        if services:
            domain_services[domain_dir.name] = services
    
    return domain_services


def validate_registry_structure(registry: Dict) -> List[str]:
    """Validate the structure of the domain registry."""
    errors = []
    
    if not isinstance(registry, dict):
        errors.append("Registry must be a dictionary")
        return errors
    
    required_domains = [
        "core", "breeding", "genomics", "phenotyping", 
        "germplasm", "environment", "spatial", "ai", "interop"
    ]
    
    for domain in required_domains:
        if domain not in registry:
            errors.append(f"Missing required domain: {domain}")
            continue
        
        domain_config = registry[domain]
        if not isinstance(domain_config, dict):
            errors.append(f"Domain '{domain}' must be a dictionary")
            continue
        
        if "services" not in domain_config:
            errors.append(f"Domain '{domain}' missing 'services' key")
        elif not isinstance(domain_config["services"], list):
            errors.append(f"Domain '{domain}' services must be a list")
    
    return errors


def validate_service_registration(
    registry: Dict, 
    flat_services: Set[str], 
    module_services: Dict[str, List[str]]
) -> List[str]:
    """Validate that all services are properly registered."""
    errors = []
    warnings = []
    
    # Get all registered services from registry
    registered_services = set()
    for domain, config in registry.items():
        if isinstance(config, dict) and "services" in config:
            for service in config["services"]:
                registered_services.add(service)
    
    # Check for unregistered services in flat directory
    unregistered_flat = flat_services - registered_services
    if unregistered_flat:
        warnings.append(
            f"⚠️  Warning: {len(unregistered_flat)} services in flat directory "
            f"not registered (migration in progress)"
        )
        for service in sorted(unregistered_flat)[:5]:  # Show first 5
            warnings.append(f"    - {service}")
        if len(unregistered_flat) > 5:
            warnings.append(f"    ... and {len(unregistered_flat) - 5} more")
    
    # Validate module services match registry
    for domain, services in module_services.items():
        if domain not in registry:
            errors.append(f"Domain module '{domain}' exists but not in registry")
            continue
        
        domain_config = registry[domain]
        if "services" not in domain_config:
            continue
        
        registered_for_domain = set(domain_config["services"])
        actual_services = set(services)
        
        # Check for services in module but not registered
        unregistered = actual_services - registered_for_domain
        if unregistered:
            errors.append(
                f"Domain '{domain}' has unregistered services: {unregistered}"
            )
    
    return errors, warnings


def main():
    """Main validation function."""
    print("🔍 Validating Domain Registry...")
    print()
    
    # Paths
    backend_dir = Path(__file__).parent.parent
    registry_path = backend_dir / "app" / "domain_registry.yaml"
    services_dir = backend_dir / "app" / "services"
    modules_dir = backend_dir / "app" / "modules"
    
    # Load registry
    registry = load_domain_registry(registry_path)
    
    # Validate structure
    print("📋 Validating registry structure...")
    structure_errors = validate_registry_structure(registry)
    if structure_errors:
        print("❌ Structure validation failed:")
        for error in structure_errors:
            print(f"   {error}")
        sys.exit(1)
    print("✅ Registry structure is valid")
    print()
    
    # Get services
    flat_services = get_services_in_directory(services_dir)
    module_services = get_services_in_modules(modules_dir)
    
    print(f"📊 Service Statistics:")
    print(f"   Flat services directory: {len(flat_services)} services")
    print(f"   Domain modules: {len(module_services)} domains with services")
    print()
    
    # Validate service registration
    print("🔍 Validating service registration...")
    errors, warnings = validate_service_registration(
        registry, flat_services, module_services
    )
    
    # Print warnings
    for warning in warnings:
        print(warning)
    
    if warnings:
        print()
    
    # Print errors
    if errors:
        print("❌ Service registration validation failed:")
        for error in errors:
            print(f"   {error}")
        sys.exit(1)
    
    print("✅ All services are properly registered")
    print()
    print("✨ Domain registry validation complete!")


if __name__ == "__main__":
    main()
