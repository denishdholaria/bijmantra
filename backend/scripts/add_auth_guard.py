#!/usr/bin/env python3
"""
Add router-level auth guard to API files that lack authentication.

Strategy: Add `dependencies=[Depends(get_current_user)]` to each router's APIRouter()
constructor, ensuring ALL endpoints in the file require authentication.

This is the cleanest approach — one change per file protects all endpoints.
"""

import re
import sys
from pathlib import Path

API_DIR = Path(__file__).parent.parent / "app" / "api" / "v2"

# Files to skip
SKIP_FILES = {
    "__init__.py",      # No endpoints
    "apex_router.py",   # Just an aggregator
}

# Files that should remain public (no auth required)
PUBLIC_FILES = {
    "languages.py",     # Language list is public
}


def file_has_auth(content: str) -> bool:
    """Check if file already imports auth dependency."""
    return "get_current_user" in content or "get_current_active_user" in content


def add_auth_to_file(filepath: Path) -> bool:
    """Add router-level auth guard to a single file."""
    content = filepath.read_text()

    if file_has_auth(content):
        return False  # Already has auth

    if filepath.name in SKIP_FILES or filepath.name in PUBLIC_FILES:
        return False

    lines = content.split("\n")
    modified = False
    new_lines = []

    # Step 1: Ensure `from app.api.deps import get_current_user` exists
    has_deps_import = "from app.api.deps import" in content
    has_fastapi_depends = "Depends" in content

    # Find the right place to add the import
    import_added = False
    deps_import_line = "from app.api.deps import get_current_user"

    for i, line in enumerate(lines):
        new_lines.append(line)

        if not import_added:
            # Add after the last import line in the import block
            # Look for existing app imports
            if line.startswith("from app.") and not has_deps_import:
                # Check if next line is not an import (end of app imports)
                if i + 1 < len(lines) and not lines[i + 1].startswith(("from ", "import ")):
                    new_lines.append(deps_import_line)
                    import_added = True
                    modified = True

    # If we didn't add it after app imports, add after all imports
    if not import_added and not has_deps_import:
        new_lines2 = []
        for i, line in enumerate(new_lines):
            new_lines2.append(line)
            if (line.startswith("from ") or line.startswith("import ")) and not import_added:
                if i + 1 < len(new_lines) and not new_lines[i + 1].startswith(("from ", "import ")):
                    new_lines2.append(deps_import_line)
                    import_added = True
                    modified = True
        new_lines = new_lines2

    content = "\n".join(new_lines)

    # Ensure Depends is imported from fastapi
    if not has_fastapi_depends:
        # Add Depends to the fastapi import
        content = re.sub(
            r'(from fastapi import .+)',
            lambda m: m.group(0) + ', Depends' if 'Depends' not in m.group(0) else m.group(0),
            content,
            count=1
        )
        modified = True

    # Step 2: Add dependencies to router = APIRouter(...)
    # Match patterns like:
    #   router = APIRouter(prefix="/xxx", tags=["XXX"])
    #   router = APIRouter()
    # But NOT if dependencies= already present

    router_pattern = re.compile(
        r'(router\s*=\s*APIRouter\s*\()'
        r'((?:(?!dependencies\s*=).)*?)'  # content without dependencies=
        r'(\))',
        re.DOTALL
    )

    def add_dependencies(match):
        prefix = match.group(1)
        args = match.group(2).strip()
        closing = match.group(3)

        if 'dependencies' in args:
            return match.group(0)  # Already has dependencies

        if args:
            # Has existing args — append dependencies
            return f'{prefix}{args}, dependencies=[Depends(get_current_user)]{closing}'
        else:
            # Empty args
            return f'{prefix}dependencies=[Depends(get_current_user)]{closing}'

    new_content = router_pattern.sub(add_dependencies, content)
    if new_content != content:
        modified = True
        content = new_content

    if modified:
        filepath.write_text(content)
        return True
    return False


def main():
    files = sorted(API_DIR.glob("*.py"))
    modified_count = 0
    skipped_count = 0
    already_auth = 0

    for filepath in files:
        if filepath.name in SKIP_FILES:
            skipped_count += 1
            continue

        original = filepath.read_text()
        if file_has_auth(original):
            already_auth += 1
            continue

        if filepath.name in PUBLIC_FILES:
            print(f"  PUBLIC  {filepath.name}")
            skipped_count += 1
            continue

        if add_auth_to_file(filepath):
            print(f"  ✅ FIXED {filepath.name}")
            modified_count += 1
        else:
            print(f"  ⚠️  SKIP  {filepath.name}")
            skipped_count += 1

    print(f"\n--- Summary ---")
    print(f"Already had auth: {already_auth}")
    print(f"Fixed: {modified_count}")
    print(f"Skipped: {skipped_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
