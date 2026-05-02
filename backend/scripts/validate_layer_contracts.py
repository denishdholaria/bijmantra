#!/usr/bin/env python3
"""
Validate Layer Contracts

This script validates that layer contracts are enforced:
- UI → API → Service → Compute/DB
- No forbidden cross-layer imports

Usage:
    python scripts/validate_layer_contracts.py
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements."""
    
    def __init__(self):
        self.imports = []
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)


def get_imports_from_file(file_path: Path) -> List[str]:
    """Extract all imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    except Exception as e:
        # Skip files that can't be parsed
        return []


def categorize_file_layer(file_path: Path, app_dir: Path) -> str:
    """Categorize a file into its architectural layer."""
    try:
        rel_path = file_path.relative_to(app_dir)
        parts = rel_path.parts
        
        # Router/API layer
        if "router.py" in str(file_path) or "api" in parts:
            return "api"
        
        # Service layer
        if "service.py" in str(file_path) or "services" in parts:
            return "service"
        
        # Model/Repository layer
        if "models.py" in str(file_path) or "models" in parts:
            return "model"
        
        # Compute layer
        if "compute" in parts:
            return "compute"
        
        # Schema layer (DTOs)
        if "schemas.py" in str(file_path) or "schemas" in parts:
            return "schema"
        
        # Core/Infrastructure
        if "core" in parts or "middleware" in parts:
            return "core"
        
        return "unknown"
    except ValueError:
        return "unknown"


def check_layer_violations(
    file_path: Path, 
    layer: str, 
    imports: List[str]
) -> List[Tuple[str, str]]:
    """Check for layer contract violations in imports."""
    violations = []
    
    # Define forbidden import patterns for each layer
    forbidden_patterns = {
        "api": [
            ("app.models", "API layer cannot import models directly"),
            ("app.modules.*.models", "API layer cannot import domain models directly"),
            ("app.modules.*.compute", "API layer cannot import compute layer"),
            ("app.db", "API layer cannot import database directly"),
        ],
        "service": [
            # Services can import models and compute, so fewer restrictions
        ],
        "schema": [
            ("app.services", "Schema layer cannot import services"),
            ("app.modules.*.services", "Schema layer cannot import domain services"),
            ("app.models", "Schema layer should not import models (use forward refs)"),
        ],
    }
    
    if layer not in forbidden_patterns:
        return violations
    
    for import_name in imports:
        for pattern, message in forbidden_patterns[layer]:
            # Simple pattern matching (can be enhanced with regex)
            if "*" in pattern:
                # Handle wildcard patterns like app.modules.*.models
                pattern_parts = pattern.split("*")
                if all(part in import_name for part in pattern_parts):
                    violations.append((import_name, message))
            else:
                # Exact or prefix match
                if import_name.startswith(pattern):
                    violations.append((import_name, message))
    
    return violations


def scan_directory_for_violations(app_dir: Path) -> Dict[str, List[Tuple]]:
    """Scan all Python files for layer contract violations."""
    violations_by_file = {}
    
    for py_file in app_dir.rglob("*.py"):
        # Skip test files and migrations
        if "test" in str(py_file) or "alembic" in str(py_file):
            continue
        
        # Skip __pycache__ and venv
        if "__pycache__" in str(py_file) or "venv" in str(py_file):
            continue
        
        # Categorize file layer
        layer = categorize_file_layer(py_file, app_dir)
        
        # Get imports
        imports = get_imports_from_file(py_file)
        
        # Check for violations
        violations = check_layer_violations(py_file, layer, imports)
        
        if violations:
            rel_path = py_file.relative_to(app_dir.parent)
            violations_by_file[str(rel_path)] = violations
    
    return violations_by_file


def check_cross_domain_imports(app_dir: Path) -> Dict[str, List[str]]:
    """Check for cross-domain imports that bypass contracts."""
    violations_by_file = {}
    modules_dir = app_dir / "modules"
    
    if not modules_dir.exists():
        return violations_by_file
    
    domains = [
        "breeding", "genomics", "phenotyping", "germplasm",
        "environment", "spatial", "ai", "interop"
    ]
    
    for domain_dir in modules_dir.iterdir():
        if not domain_dir.is_dir() or domain_dir.name not in domains:
            continue
        
        for py_file in domain_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            imports = get_imports_from_file(py_file)
            violations = []
            
            for import_name in imports:
                # Check if importing from another domain
                for other_domain in domains:
                    if other_domain == domain_dir.name:
                        continue
                    
                    if f"app.modules.{other_domain}" in import_name:
                        # Cross-domain import detected
                        violations.append(
                            f"Cross-domain import: {domain_dir.name} → {other_domain}"
                        )
            
            if violations:
                rel_path = py_file.relative_to(app_dir.parent)
                violations_by_file[str(rel_path)] = violations
    
    return violations_by_file


def main():
    """Main validation function."""
    print("🔍 Validating Layer Contracts...")
    print()
    
    # Paths
    backend_dir = Path(__file__).parent.parent
    app_dir = backend_dir / "app"
    
    # Check layer contract violations
    print("📋 Checking layer contract violations...")
    layer_violations = scan_directory_for_violations(app_dir)
    
    if layer_violations:
        print(f"⚠️  Found {len(layer_violations)} files with layer violations:")
        print()
        for file_path, violations in list(layer_violations.items())[:10]:
            print(f"   {file_path}:")
            for import_name, message in violations:
                print(f"      ❌ {import_name}")
                print(f"         {message}")
        
        if len(layer_violations) > 10:
            remaining = len(layer_violations) - 10
            print(f"   ... and {remaining} more files")
        print()
    else:
        print("✅ No layer contract violations detected")
        print()
    
    # Check cross-domain imports
    print("🔍 Checking cross-domain imports...")
    cross_domain_violations = check_cross_domain_imports(app_dir)
    
    if cross_domain_violations:
        print(f"⚠️  Found {len(cross_domain_violations)} files with cross-domain imports:")
        print()
        for file_path, violations in list(cross_domain_violations.items())[:10]:
            print(f"   {file_path}:")
            for violation in violations:
                print(f"      ❌ {violation}")
        
        if len(cross_domain_violations) > 10:
            remaining = len(cross_domain_violations) - 10
            print(f"   ... and {remaining} more files")
        print()
        print("   Note: Cross-domain communication should use event_bus or explicit interfaces")
        print()
    else:
        print("✅ No cross-domain import violations detected")
        print()
    
    # Summary
    total_violations = len(layer_violations) + len(cross_domain_violations)
    
    if total_violations > 0:
        print("📊 Summary:")
        print(f"   Layer violations: {len(layer_violations)} files")
        print(f"   Cross-domain violations: {len(cross_domain_violations)} files")
        print(f"   Total: {total_violations} files with violations")
        print()
        print("⚠️  Warning: Architecture violations detected")
        print("   These should be fixed during migration phases")
        print()
        # Don't fail CI during migration - just warn
        # sys.exit(1)
    else:
        print("✅ All layer contracts are properly enforced")
        print()
    
    print("✨ Layer contract validation complete!")


if __name__ == "__main__":
    main()
