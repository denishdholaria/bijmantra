#!/usr/bin/env python3
"""
Extract all API endpoints from BijMantra backend code.
Generates a complete inventory for documentation.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_endpoints(base_path: str) -> list[dict]:
    """Extract all @router decorated endpoints from Python files."""
    endpoints = []
    
    # Pattern to match @router.method("path", ...)
    pattern = re.compile(
        r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    for root, dirs, files in os.walk(base_path):
        # Skip __pycache__ and venv
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv', '.git')]
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = Path(root) / file
            rel_path = str(filepath.relative_to(base_path))
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for match in pattern.finditer(content):
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    # Determine prefix based on file location
                    if 'brapi' in rel_path:
                        if 'extensions' in rel_path:
                            prefix = '/brapi/v2/extensions/iot'
                        else:
                            prefix = '/brapi/v2'
                    elif 'auth.py' in rel_path:
                        prefix = '/api'
                    else:
                        prefix = '/api/v2'
                    
                    full_path = f"{prefix}{path}" if not path.startswith('/') else f"{prefix}{path}"
                    
                    endpoints.append({
                        'method': method,
                        'path': full_path,
                        'file': rel_path
                    })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return endpoints

def categorize_endpoints(endpoints: list[dict]) -> dict:
    """Group endpoints by category."""
    categories = defaultdict(list)
    
    for ep in endpoints:
        file = ep['file']
        
        if 'brapi' in file:
            if 'extensions' in file:
                cat = 'BrAPI IoT Extensions'
            elif 'search' in file:
                cat = 'BrAPI Search'
            else:
                cat = 'BrAPI Core'
        elif 'auth.py' in file:
            cat = 'Authentication'
        elif 'v2/' in file:
            # Extract category from filename
            filename = Path(file).stem
            cat = filename.replace('_', ' ').title()
        else:
            cat = 'Other'
            
        categories[cat].append(ep)
    
    return dict(sorted(categories.items()))

def generate_markdown(endpoints: list[dict], categories: dict) -> str:
    """Generate markdown documentation."""
    lines = [
        "# BijMantra API Endpoint Inventory",
        "",
        f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total Endpoints:** {len(endpoints)}",
        "**Method:** Automated extraction from source code",
        "",
        "---",
        "",
        "## Summary by Category",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    
    for cat, eps in sorted(categories.items(), key=lambda x: -len(x[1])):
        lines.append(f"| {cat} | {len(eps)} |")
    
    lines.extend(["", "---", ""])
    
    # Method summary
    method_counts = defaultdict(int)
    for ep in endpoints:
        method_counts[ep['method']] += 1
    
    lines.extend([
        "## Summary by HTTP Method",
        "",
        "| Method | Count |",
        "|--------|-------|",
    ])
    for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        if method in method_counts:
            lines.append(f"| {method} | {method_counts[method]} |")
    
    lines.extend(["", "---", ""])
    
    # Detailed listing by category
    lines.append("## Complete Endpoint Listing")
    lines.append("")
    
    for cat, eps in sorted(categories.items()):
        lines.append(f"### {cat} ({len(eps)} endpoints)")
        lines.append("")
        lines.append("| Method | Path | Source File |")
        lines.append("|--------|------|-------------|")
        
        for ep in sorted(eps, key=lambda x: (x['path'], x['method'])):
            lines.append(f"| {ep['method']} | `{ep['path']}` | {ep['file']} |")
        
        lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    base = Path(__file__).parent.parent / "backend" / "app"
    
    print(f"Scanning {base}...")
    endpoints = extract_endpoints(str(base))
    print(f"Found {len(endpoints)} endpoints")
    
    categories = categorize_endpoints(endpoints)
    print(f"Categorized into {len(categories)} categories")
    
    markdown = generate_markdown(endpoints, categories)
    
    output_path = Path(__file__).parent.parent / "docs" / "api" / "ENDPOINT_INVENTORY.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"Written to {output_path}")
