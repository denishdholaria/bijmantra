#!/usr/bin/env python3
"""
Fix test mock patch paths after service migration.
Updates @patch() and patch() calls to use new module paths.
"""

import re
from pathlib import Path

# Mapping of old service paths to new module paths
MOCK_PATH_MAPPINGS = {
    # Infra services
    'app.services.infra.saml_oidc_auth_provider': 'app.modules.core.services.infra.saml_oidc_auth_provider',
    'app.services.infra.mqtt_lorawan_ingestion_node': 'app.modules.core.services.infra.mqtt_lorawan_ingestion_node',
    
    # ML services
    'app.services.ml_bounding_box_extractor': 'app.modules.ai.services.ml_bounding_box_extractor_service',
    
    # Compliance services
    'app.services.compliance.batch': 'app.modules.core.services.compliance.batch_service',
    
    # Weather services
    'app.services.weather_integration_service': 'app.modules.environment.services.weather_integration_service',
    
    # Progress tracker
    'app.services.progress_tracker': 'app.modules.core.services.progress_tracker_service',
    
    # Analytics services
    'app.services.analytics.etl_phenotype_extractor': 'app.modules.core.services.analytics.etl_phenotype_extractor_service',
    'app.services.analytics.custom_report_weasyprint_engine': 'app.modules.core.services.analytics.custom_report_weasyprint_engine_service',
}


def replace_in_content(content: str, old_path: str, new_path: str) -> tuple[str, int]:
    """Replace old path with new path, handling both module and function/class references."""
    count = 0
    
    # Pattern 1: patch("app.services.X.function_name")
    # Pattern 2: patch("app.services.X")
    # We need to match the path up to the old_path, then optionally a dot and more
    pattern = rf'(patch\(["\']){re.escape(old_path)}(\.[a-zA-Z_][a-zA-Z0-9_]*)?(["\'])'
    
    def replacer(match):
        nonlocal count
        count += 1
        prefix = match.group(1)  # patch("
        suffix_part = match.group(2) or ''  # .function_name or empty
        quote = match.group(3)  # ")
        return f'{prefix}{new_path}{suffix_part}{quote}'
    
    new_content = re.sub(pattern, replacer, content)
    return new_content, count


def fix_mock_patches_in_file(file_path: Path) -> tuple[int, list[str]]:
    """Fix mock patch paths in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        changes = []
        
        for old_path, new_path in MOCK_PATH_MAPPINGS.items():
            new_content, count = replace_in_content(content, old_path, new_path)
            if count > 0:
                content = new_content
                changes.append(f"  {old_path} -> {new_path} ({count} occurrences)")
        
        if content != original_content:
            file_path.write_text(content)
            return len(changes), changes
        
        return 0, []
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []


def main():
    """Main function to fix all test files."""
    backend_tests = Path("backend/tests")
    
    if not backend_tests.exists():
        print(f"Error: {backend_tests} not found")
        return
    
    print("Fixing test mock patch paths...")
    print("=" * 80)
    
    total_files_changed = 0
    total_changes = 0
    
    # Find all Python test files
    test_files = list(backend_tests.rglob("test_*.py"))
    
    for test_file in test_files:
        if "__pycache__" in str(test_file):
            continue
        
        change_count, changes = fix_mock_patches_in_file(test_file)
        
        if change_count > 0:
            total_files_changed += 1
            total_changes += change_count
            print(f"\n✓ {test_file.relative_to('backend/tests')}")
            for change in changes:
                print(change)
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Files changed: {total_files_changed}")
    print(f"  Total changes: {total_changes}")
    print("\nDone!")


if __name__ == "__main__":
    main()
