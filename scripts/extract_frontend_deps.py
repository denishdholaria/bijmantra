#!/usr/bin/env python3
"""
Extract directed file-level dependency graph from Bijmantra frontend.
Produces JSON suitable for DAG construction, cycle detection, and architectural analysis.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# Frontend root directory
FRONTEND_ROOT = Path("frontend/src")

# Patterns for extracting imports
ES_IMPORT_PATTERN = re.compile(
    r'''import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*)\s+from\s+['"]([^'"]+)['"]'''
)
DYNAMIC_IMPORT_PATTERN = re.compile(
    r'''import\s*\(\s*['"]([^'"]+)['"]\s*\)'''
)
REQUIRE_PATTERN = re.compile(
    r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)'''
)

# File type classification
RUNTIME_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.mjs'}
TEST_PATTERNS = {'.test.', '.spec.', '__tests__', '__mocks__'}
TOOLING_PATHS = {'scripts/', 'e2e/', 'verification/'}
CONFIG_FILES = {'vite.config', 'vitest.config', 'postcss.config', 'eslint.config', 
                'tailwind.config', 'capacitor.config', 'tsconfig'}

# Layer classification patterns
UI_PATHS = {'pages/', 'components/'}
APPLICATION_PATHS = {'hooks/', 'services/', 'store/', 'stores/', 'features/'}
DOMAIN_PATHS = {'divisions/', 'lib/genomics', 'lib/breeding'}
INFRA_PATHS = {'api/', 'lib/api', 'wasm/', 'lib/sync', 'lib/tracing', 'lib/realtime'}


@dataclass
class Node:
    id: str
    label: str
    path: str
    type: str  # runtime | test | tooling | config
    layer: str  # ui | application | domain | infra | unknown


@dataclass
class Edge:
    source: str
    target: str
    type: str  # imports | dynamic_import | require
    confidence: str  # high | medium | low


def classify_file_type(file_path: str) -> str:
    """Classify file as runtime, test, tooling, or config."""
    path_lower = file_path.lower()
    
    # Check for config files
    for config in CONFIG_FILES:
        if config in path_lower:
            return "config"
    
    # Check for tooling paths
    for tooling in TOOLING_PATHS:
        if tooling in path_lower:
            return "tooling"
    
    # Check for test patterns
    for test_pattern in TEST_PATTERNS:
        if test_pattern in path_lower:
            return "test"
    
    return "runtime"


def classify_layer(file_path: str) -> str:
    """Classify file into architectural layer."""
    path_lower = file_path.lower()
    
    # Check UI layer first (most specific)
    for ui_path in UI_PATHS:
        if ui_path in path_lower:
            return "ui"
    
    # Check application layer
    for app_path in APPLICATION_PATHS:
        if app_path in path_lower:
            return "application"
    
    # Check domain layer
    for domain_path in DOMAIN_PATHS:
        if domain_path in path_lower:
            return "domain"
    
    # Check infra layer
    for infra_path in INFRA_PATHS:
        if infra_path in path_lower:
            return "infra"
    
    return "unknown"


def resolve_import_path(import_path: str, source_file: str, frontend_root: Path, project_root: Path) -> str | None:
    """
    Resolve an import path to an actual file path relative to project root.
    Returns None if the import is external (node_modules) or cannot be resolved.
    """
    # Skip external imports (node_modules)
    if not import_path.startswith('.') and not import_path.startswith('@/'):
        # Check if it's a known internal path starting with src/
        if import_path.startswith('src/'):
            import_path = import_path[4:]  # Remove 'src/' prefix
        else:
            return None  # External module
    
    # Handle @/ alias (maps to frontend/src)
    if import_path.startswith('@/'):
        import_path = 'src/' + import_path[2:]  # Replace @/ with src/
    
    # Handle relative imports
    if import_path.startswith('.'):
        source_dir = Path(source_file).parent
        resolved = (source_dir / import_path).resolve()
        try:
            relative = resolved.relative_to(project_root.resolve())
            import_path = str(relative)
        except ValueError:
            return None
    
    # Normalize path
    import_path = import_path.lstrip('/')
    
    # Try to resolve to actual file
    possible_paths = [
        import_path,
        f"{import_path}.ts",
        f"{import_path}.tsx",
        f"{import_path}.js",
        f"{import_path}.jsx",
        f"{import_path}.mjs",
        f"{import_path}/index.ts",
        f"{import_path}/index.tsx",
        f"{import_path}/index.js",
    ]
    
    for possible in possible_paths:
        full_path = project_root / possible
        if full_path.exists():
            return possible
    
    return None


def extract_imports(file_path: Path) -> List[Tuple[str, str]]:
    """
    Extract all imports from a file.
    Returns list of (import_path, import_type) tuples.
    """
    imports = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return imports
    
    # Extract ES imports
    for match in ES_IMPORT_PATTERN.finditer(content):
        imports.append((match.group(1), 'imports'))
    
    # Extract dynamic imports
    for match in DYNAMIC_IMPORT_PATTERN.finditer(content):
        imports.append((match.group(1), 'dynamic_import'))
    
    # Extract require statements
    for match in REQUIRE_PATTERN.finditer(content):
        imports.append((match.group(1), 'require'))
    
    return imports


def build_dependency_graph(frontend_root: Path, project_root: Path) -> Tuple[List[Node], List[Edge]]:
    """Build the complete dependency graph."""
    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []
    edge_set: Set[Tuple[str, str, str]] = set()  # For deduplication
    
    # Collect all TypeScript/JavaScript files
    all_files = []
    for ext in RUNTIME_EXTENSIONS:
        all_files.extend(frontend_root.rglob(f"*{ext}"))
    
    # Also include config files outside src
    config_files = [
        project_root / "vite.config.ts",
        project_root / "vitest.config.ts",
        project_root / "postcss.config.js",
        project_root / "eslint.config.mjs",
        project_root / "capacitor.config.ts",
        project_root / "tailwind.config.cjs",
    ]
    all_files.extend([f for f in config_files if f.exists()])
    
    # Include e2e tests
    e2e_root = project_root / "e2e"
    if e2e_root.exists():
        for ext in RUNTIME_EXTENSIONS:
            all_files.extend(e2e_root.rglob(f"*{ext}"))
    
    # Include scripts
    scripts_root = project_root / "scripts"
    if scripts_root.exists():
        for ext in ['.ts', '.mjs', '.js']:
            all_files.extend(scripts_root.rglob(f"*{ext}"))
    
    print(f"Found {len(all_files)} files to analyze...")
    
    # First pass: create all nodes
    for file_path in all_files:
        try:
            relative_path = file_path.relative_to(project_root)
        except ValueError:
            continue
        
        path_str = str(relative_path)
        node_id = path_str.replace('/', '_').replace('.', '_').replace('-', '_')
        
        # Skip node_modules
        if 'node_modules' in path_str:
            continue
        
        # Skip dist/build
        if 'dist/' in path_str or path_str.startswith('dist'):
            continue
        
        node = Node(
            id=node_id,
            label=file_path.name,
            path=path_str,
            type=classify_file_type(path_str),
            layer=classify_layer(path_str)
        )
        nodes[node_id] = node
    
    print(f"Created {len(nodes)} nodes")
    
    # Second pass: create edges
    for file_path in all_files:
        try:
            source_relative = file_path.relative_to(project_root)
        except ValueError:
            continue
        
        source_path_str = str(source_relative)
        source_id = source_path_str.replace('/', '_').replace('.', '_').replace('-', '_')
        
        if source_id not in nodes:
            continue
        
        # Extract imports
        imports = extract_imports(file_path)
        
        for import_path, import_type in imports:
            # Resolve the import to an actual file
            resolved = resolve_import_path(import_path, source_path_str, frontend_root, project_root)
            
            if resolved:
                target_id = resolved.replace('/', '_').replace('.', '_').replace('-', '_')
                
                # Check if target exists in our nodes
                if target_id in nodes:
                    edge_key = (source_id, target_id, import_type)
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append(Edge(
                            source=source_id,
                            target=target_id,
                            type=import_type,
                            confidence='high'  # All extracted imports are high confidence
                        ))
    
    print(f"Created {len(edges)} edges")
    
    return list(nodes.values()), edges


def main():
    project_root = Path("frontend")
    frontend_root = project_root / "src"
    
    if not frontend_root.exists():
        print(f"Error: {frontend_root} does not exist")
        return
    
    print("Building dependency graph for Bijmantra frontend...")
    nodes, edges = build_dependency_graph(frontend_root, project_root)
    
    # Build output JSON
    output = {
        "directed": True,
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges]
    }
    
    # Write to file
    output_path = Path("frontend-dependency-graph.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDependency graph written to {output_path}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")
    
    # Print summary statistics
    type_counts = defaultdict(int)
    layer_counts = defaultdict(int)
    
    for node in nodes:
        type_counts[node.type] += 1
        layer_counts[node.layer] += 1
    
    print("\nNode types:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")
    
    print("\nNode layers:")
    for l, count in sorted(layer_counts.items()):
        print(f"  {l}: {count}")


if __name__ == "__main__":
    main()
