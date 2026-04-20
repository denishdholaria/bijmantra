"""
Generate comprehensive API Registry documentation from OpenAPI metadata.

This script extracts all API endpoints from the FastAPI application's OpenAPI schema
and generates a comprehensive registry organized by domain.

The registry includes:
- Endpoint path, method, owner, purpose
- Authentication requirements
- Rate limits (if configured)
- Source file location
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[3]
BACKEND_APP = ROOT / "backend" / "app"
DOC_PATH = ROOT / "docs" / "api" / "API_REGISTRY.md"
REGISTRY_JSON_PATH = ROOT / "docs" / "api" / "API_REGISTRY.json"


# Domain mapping based on URL prefixes
DOMAIN_MAPPING = {
    "/api/v2/core": "core",
    "/api/v2/breeding": "breeding",
    "/api/v2/genomics": "genomics",
    "/api/v2/phenotyping": "phenotyping",
    "/api/v2/germplasm": "germplasm",
    "/api/v2/environment": "environment",
    "/api/v2/spatial": "spatial",
    "/api/v2/ai": "ai",
    "/api/v2/interop": "interop",
    "/brapi/v2": "interop",
    "/api/auth": "core",
    "/api/v1": "legacy",
}


def get_domain_from_path(path: str) -> str:
    """Determine domain from endpoint path."""
    # Check for exact matches first
    for prefix, domain in DOMAIN_MAPPING.items():
        if path.startswith(prefix):
            return domain
    
    # Check for specific patterns
    if "/weather" in path or "/climate" in path or "/gdd" in path:
        return "environment"
    if "/soil" in path:
        return "spatial"
    if "/veena" in path or "/chat" in path or "/reevu" in path:
        return "ai"
    if "/cross" in path or "/trial" in path or "/breeding" in path:
        return "breeding"
    if "/gwas" in path or "/genomic" in path or "/marker" in path:
        return "genomics"
    if "/observation" in path or "/phenotype" in path or "/image" in path:
        return "phenotyping"
    if "/germplasm" in path or "/seed" in path:
        return "germplasm"
    if "/spatial" in path or "/maps" in path or "/location" in path:
        return "spatial"
    
    # Default to core for unmatched paths
    return "core"


def find_source_file(path: str, method: str) -> str:
    """Find the source file that defines an endpoint."""
    # Search in modules first
    for module_dir in (BACKEND_APP / "modules").iterdir():
        if not module_dir.is_dir():
            continue
        
        router_file = module_dir / "router.py"
        if router_file.exists():
            content = router_file.read_text(encoding="utf-8", errors="ignore")
            # Look for route decorator with this path
            pattern = rf'@\w+\.{method.lower()}\(["\'].*{re.escape(path.split("/")[-1])}.*["\']\)'
            if re.search(pattern, content, re.IGNORECASE):
                return str(router_file.relative_to(ROOT))
    
    # Search in api directory
    for api_file in (BACKEND_APP / "api").rglob("*.py"):
        content = api_file.read_text(encoding="utf-8", errors="ignore")
        pattern = rf'@\w+\.{method.lower()}\(["\'].*{re.escape(path.split("/")[-1])}.*["\']\)'
        if re.search(pattern, content, re.IGNORECASE):
            return str(api_file.relative_to(ROOT))
    
    return "unknown"


def extract_routes_from_openapi() -> list[dict[str, Any]]:
    """Extract routes from FastAPI OpenAPI schema."""
    try:
        # Import the FastAPI app
        from app.main import app
        
        # Get OpenAPI schema
        openapi_schema = app.openapi()
        
        routes = []
        for path, path_item in openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
                    continue
                
                # Extract metadata
                summary = operation.get("summary", "")
                description = operation.get("description", "")
                tags = operation.get("tags", [])
                operation_id = operation.get("operationId", "")
                
                # Determine authentication requirement
                security = operation.get("security", [])
                requires_auth = len(security) > 0
                
                # Determine domain
                domain = get_domain_from_path(path)
                
                # Find source file
                source = find_source_file(path, method)
                
                routes.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": summary or description or operation_id,
                    "domain": domain,
                    "tags": tags,
                    "requires_auth": requires_auth,
                    "source": source,
                    "operation_id": operation_id,
                })
        
        return sorted(routes, key=lambda r: (r["domain"], r["path"], r["method"]))
    
    except Exception as e:
        print(f"Error extracting routes from OpenAPI: {e}")
        print("Falling back to static analysis...")
        return extract_routes_static()


def extract_routes_static() -> list[dict[str, Any]]:
    """Fallback: Extract routes by statically scanning FastAPI route declarations."""
    routes: list[dict[str, Any]] = []
    pattern = re.compile(r'@(?:\w+\.)?(get|post|put|patch|delete|options)\(\s*["\']([^"\']+)["\']')
    
    # Scan modules
    for py_file in BACKEND_APP.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            rel_source = str(py_file.relative_to(ROOT))
            
            for method_raw, raw_path in pattern.findall(text):
                method = method_raw.upper()
                path = raw_path
                
                # Normalize path
                if not path.startswith("/"):
                    path = "/" + path
                
                # Add prefix based on file location
                if "brapi" in rel_source:
                    if not path.startswith("/brapi/v2"):
                        path = "/brapi/v2" + path
                elif "api/v2" in rel_source:
                    if not path.startswith("/api/v2") and not path.startswith("/brapi/v2"):
                        path = "/api/v2" + path
                elif "api/v1" in rel_source:
                    if not path.startswith("/api/v1"):
                        path = "/api/v1" + path
                
                domain = get_domain_from_path(path)
                
                routes.append({
                    "method": method,
                    "path": path,
                    "summary": "",
                    "domain": domain,
                    "tags": [],
                    "requires_auth": True,  # Assume auth required by default
                    "source": rel_source,
                    "operation_id": "",
                })
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
            continue
    
    return sorted(routes, key=lambda r: (r["domain"], r["path"], r["method"]))


def build_markdown(routes: list[dict[str, Any]]) -> str:
    """Build markdown documentation from routes."""
    # Group routes by domain
    routes_by_domain = defaultdict(list)
    for route in routes:
        routes_by_domain[route["domain"]].append(route)
    
    # Domain descriptions
    domain_descriptions = {
        "core": "Authentication, authorization, tenants, and platform infrastructure",
        "breeding": "Breeding programs, crosses, trials, breeding values, and selection",
        "genomics": "GWAS, genomic selection, molecular breeding, and genetic analysis",
        "phenotyping": "Field observations, phenotype analysis, image analysis, and vision systems",
        "germplasm": "Seed and genetic resource management, germplasm passport, and inventory",
        "environment": "Weather, climate, environmental physics, and field environment",
        "spatial": "Geospatial analytics, maps, location services, and spatial analysis",
        "ai": "Veena AI assistant, RAG, ML services, and cognitive functions",
        "interop": "BrAPI and external integrations, data exchange standards",
        "legacy": "Legacy API endpoints (v1)",
    }
    
    lines = [
        "# API Registry",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        f"**Total Endpoints:** {len(routes)}",
        "",
        "This registry documents all API endpoints in the BijMantra platform, organized by domain.",
        "",
        "## Table of Contents",
        "",
    ]
    
    # Add TOC
    for domain in sorted(routes_by_domain.keys()):
        count = len(routes_by_domain[domain])
        lines.append(f"- [{domain.title()} Domain](#-domain) ({count} endpoints)")
    
    lines.extend(["", "---", ""])
    
    # Add domain sections
    for domain in sorted(routes_by_domain.keys()):
        domain_routes = routes_by_domain[domain]
        description = domain_descriptions.get(domain, "")
        
        lines.extend([
            f"## {domain.title()} Domain",
            "",
            f"**Description:** {description}",
            "",
            f"**Endpoints:** {len(domain_routes)}",
            "",
            "| Method | Path | Purpose | Auth | Source |",
            "|--------|------|---------|------|--------|",
        ])
        
        for route in domain_routes:
            method = route["method"]
            path = route["path"]
            summary = route["summary"] or "-"
            auth = "✓" if route["requires_auth"] else "✗"
            source = route["source"]
            
            # Truncate long summaries
            if len(summary) > 80:
                summary = summary[:77] + "..."
            
            # Truncate long paths for display
            display_path = path
            if len(display_path) > 60:
                display_path = display_path[:57] + "..."
            
            lines.append(
                f"| `{method}` | `{display_path}` | {summary} | {auth} | `{source}` |"
            )
        
        lines.extend(["", ""])
    
    # Add footer
    lines.extend([
        "---",
        "",
        "## Legend",
        "",
        "- **Auth**: ✓ = Authentication required, ✗ = Public endpoint",
        "- **Source**: File path relative to repository root",
        "",
        "## Automated Regeneration",
        "",
        "This document is automatically generated from the FastAPI OpenAPI schema.",
        "",
        "To regenerate:",
        "",
        "```bash",
        "cd backend",
        "python -m app.scripts.generate_api_registry",
        "```",
        "",
        "## CI/CD Integration",
        "",
        "This registry is automatically regenerated on API changes via pre-commit hook.",
        "",
        "See `.git/hooks/pre-commit` for implementation details.",
        "",
    ])
    
    return "\n".join(lines)


def build_json(routes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build JSON registry from routes."""
    routes_by_domain = defaultdict(list)
    for route in routes:
        routes_by_domain[route["domain"]].append(route)
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_endpoints": len(routes),
        "domains": {
            domain: {
                "endpoint_count": len(domain_routes),
                "endpoints": domain_routes,
            }
            for domain, domain_routes in sorted(routes_by_domain.items())
        },
    }


def main() -> int:
    """Main entry point."""
    print("Generating API Registry...")
    
    # Extract routes
    print("Extracting routes from OpenAPI schema...")
    routes = extract_routes_from_openapi()
    
    if not routes:
        print("No routes found!")
        return 1
    
    print(f"Found {len(routes)} endpoints")
    
    # Generate markdown
    print("Generating markdown documentation...")
    markdown = build_markdown(routes)
    
    # Generate JSON
    print("Generating JSON registry...")
    json_data = build_json(routes)
    
    # Write files
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing {DOC_PATH}...")
    DOC_PATH.write_text(markdown, encoding="utf-8")
    
    print(f"Writing {REGISTRY_JSON_PATH}...")
    REGISTRY_JSON_PATH.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print("✓ API Registry generated successfully!")
    print(f"  - Markdown: {DOC_PATH}")
    print(f"  - JSON: {REGISTRY_JSON_PATH}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
