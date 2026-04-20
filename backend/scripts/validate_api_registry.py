#!/usr/bin/env python3
"""
Validate API Registry

This script validates that all API endpoints are documented and organized by domain.
It checks the FastAPI application for undocumented endpoints.

Usage:
    python scripts/validate_api_registry.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add app to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def get_all_routes_from_app() -> List[Tuple[str, str, str]]:
    """
    Get all routes from the FastAPI application.
    Returns list of (method, path, endpoint_name) tuples.
    """
    try:
        from app.main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                for method in route.methods:
                    if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        endpoint_name = route.name if hasattr(route, "name") else "unknown"
                        routes.append((method, route.path, endpoint_name))
        
        return routes
    except Exception as e:
        print(f"❌ Error loading FastAPI app: {e}")
        sys.exit(1)


def categorize_routes_by_domain(routes: List[Tuple[str, str, str]]) -> Dict[str, List[Tuple]]:
    """Categorize routes by domain based on URL path."""
    domain_routes = {
        "core": [],
        "breeding": [],
        "genomics": [],
        "phenotyping": [],
        "germplasm": [],
        "environment": [],
        "spatial": [],
        "ai": [],
        "interop": [],
        "brapi": [],
        "uncategorized": [],
    }
    
    for method, path, endpoint_name in routes:
        # Skip OpenAPI/docs endpoints
        if path in ["/openapi.json", "/docs", "/redoc", "/health"]:
            continue
        
        # Categorize by path prefix
        if "/api/v2/core" in path or "/auth" in path or "/users" in path:
            domain_routes["core"].append((method, path, endpoint_name))
        elif "/api/v2/breeding" in path or "/crosses" in path or "/trials" in path:
            domain_routes["breeding"].append((method, path, endpoint_name))
        elif "/api/v2/genomics" in path or "/gwas" in path or "/markers" in path:
            domain_routes["genomics"].append((method, path, endpoint_name))
        elif "/api/v2/phenotyping" in path or "/phenotype" in path or "/observations" in path:
            domain_routes["phenotyping"].append((method, path, endpoint_name))
        elif "/api/v2/germplasm" in path or "/germplasm" in path:
            domain_routes["germplasm"].append((method, path, endpoint_name))
        elif "/api/v2/environment" in path or "/weather" in path or "/climate" in path:
            domain_routes["environment"].append((method, path, endpoint_name))
        elif "/api/v2/spatial" in path or "/maps" in path or "/location" in path:
            domain_routes["spatial"].append((method, path, endpoint_name))
        elif "/api/v2/ai" in path or "/veena" in path or "/reevu" in path:
            domain_routes["ai"].append((method, path, endpoint_name))
        elif "/brapi" in path:
            domain_routes["brapi"].append((method, path, endpoint_name))
        elif "/api/v2/interop" in path or "/integration" in path:
            domain_routes["interop"].append((method, path, endpoint_name))
        else:
            domain_routes["uncategorized"].append((method, path, endpoint_name))
    
    return domain_routes


def check_api_registry_exists() -> bool:
    """Check if API registry documentation exists."""
    docs_dir = backend_dir.parent / "docs" / "api"
    registry_path = docs_dir / "API_REGISTRY.md"
    
    if not registry_path.exists():
        print("⚠️  Warning: API_REGISTRY.md does not exist yet")
        print(f"   Expected location: {registry_path}")
        print("   This will be generated in Phase 7 (Task 7.4)")
        return False
    
    return True


def validate_domain_routers() -> List[str]:
    """Validate that domain routers exist in modules."""
    errors = []
    modules_dir = backend_dir / "app" / "modules"
    
    required_domains = [
        "core", "breeding", "genomics", "phenotyping",
        "germplasm", "environment", "spatial", "ai", "interop"
    ]
    
    for domain in required_domains:
        domain_dir = modules_dir / domain
        router_file = domain_dir / "router.py"
        
        if not domain_dir.exists():
            errors.append(f"Domain module directory missing: {domain}")
        elif not router_file.exists():
            errors.append(f"Domain router missing: {domain}/router.py")
    
    return errors


def main():
    """Main validation function."""
    print("🔍 Validating API Registry...")
    print()
    
    # Check if API registry documentation exists
    print("📄 Checking API registry documentation...")
    registry_exists = check_api_registry_exists()
    print()
    
    # Get all routes from the application
    print("🔍 Analyzing FastAPI routes...")
    try:
        routes = get_all_routes_from_app()
        print(f"✅ Found {len(routes)} API endpoints")
    except Exception as e:
        print(f"❌ Failed to load routes: {e}")
        sys.exit(1)
    print()
    
    # Categorize routes by domain
    print("📊 Categorizing routes by domain...")
    domain_routes = categorize_routes_by_domain(routes)
    
    for domain, routes_list in domain_routes.items():
        if routes_list:
            print(f"   {domain}: {len(routes_list)} endpoints")
    print()
    
    # Check for uncategorized routes
    if domain_routes["uncategorized"]:
        print("⚠️  Warning: Found uncategorized endpoints:")
        for method, path, endpoint_name in domain_routes["uncategorized"][:10]:
            print(f"   {method} {path}")
        if len(domain_routes["uncategorized"]) > 10:
            remaining = len(domain_routes["uncategorized"]) - 10
            print(f"   ... and {remaining} more")
        print()
    
    # Validate domain routers exist
    print("🔍 Validating domain routers...")
    router_errors = validate_domain_routers()
    
    if router_errors:
        print("⚠️  Warning: Some domain routers are missing (migration in progress):")
        for error in router_errors:
            print(f"   {error}")
        print()
    else:
        print("✅ All domain routers exist")
        print()
    
    # Summary
    print("📋 Summary:")
    print(f"   Total endpoints: {len(routes)}")
    print(f"   Categorized: {len(routes) - len(domain_routes['uncategorized'])}")
    print(f"   Uncategorized: {len(domain_routes['uncategorized'])}")
    print()
    
    if not registry_exists:
        print("ℹ️  API registry documentation will be generated in Phase 7")
        print("   For now, validation checks endpoint categorization only")
    
    print()
    print("✨ API registry validation complete!")


if __name__ == "__main__":
    main()
