#!/usr/bin/env python3
"""
Phase 2: Add router-level auth to files that have auth on SOME but not ALL endpoints,
plus the BrAPI aggregator routers and social.py.
"""
import re
from pathlib import Path

BASE = Path(__file__).parent.parent

# ─── Fix BrAPI aggregator routers ───
def fix_brapi_routers():
    """Add dependencies to brapi_germplasm_router and brapi_genotyping_router."""

    # router.py
    rpath = BASE / "app" / "api" / "brapi" / "router.py"
    content = rpath.read_text()
    if "dependencies" not in content:
        content = content.replace(
            "from fastapi import APIRouter",
            "from fastapi import APIRouter, Depends\nfrom app.api.deps import get_current_user"
        )
        content = content.replace(
            'brapi_germplasm_router = APIRouter(tags=["BrAPI Germplasm"])',
            'brapi_germplasm_router = APIRouter(tags=["BrAPI Germplasm"], dependencies=[Depends(get_current_user)])'
        )
        rpath.write_text(content)
        print("  ✅ Fixed brapi/router.py")

    # genotyping_router.py
    gpath = BASE / "app" / "api" / "brapi" / "genotyping_router.py"
    content = gpath.read_text()
    if "dependencies" not in content:
        content = content.replace(
            "from fastapi import APIRouter",
            "from fastapi import APIRouter, Depends\nfrom app.api.deps import get_current_user"
        )
        content = content.replace(
            'brapi_genotyping_router = APIRouter(tags=["BrAPI Genotyping"])',
            'brapi_genotyping_router = APIRouter(tags=["BrAPI Genotyping"], dependencies=[Depends(get_current_user)])'
        )
        gpath.write_text(content)
        print("  ✅ Fixed brapi/genotyping_router.py")


def add_router_deps(filepath: Path):
    """Add dependencies=[Depends(get_current_user)] to router in a v2 file."""
    content = filepath.read_text()

    # Skip if router already has dependencies
    # Find the router line
    router_match = re.search(r'router\s*=\s*APIRouter\(([^)]*)\)', content)
    if not router_match:
        print(f"  ⚠️  No router found in {filepath.name}")
        return

    if "dependencies" in router_match.group(0):
        print(f"  SKIP {filepath.name} (already has dependencies)")
        return

    # Add import if missing
    if "from app.api.deps import get_current_user" not in content and \
       "from app.api.v2.dependencies import get_current_user" not in content:
        # Add before router line
        content = content.replace(
            router_match.group(0),
            f"from app.api.deps import get_current_user\n\n{router_match.group(0)}"
        )

    # Ensure Depends is imported
    if "Depends" not in content.split("router")[0]:
        content = re.sub(
            r'(from fastapi import )(.*)',
            lambda m: m.group(0) if 'Depends' in m.group(2) else f'{m.group(1)}{m.group(2)}, Depends',
            content,
            count=1
        )

    # Add dependencies to router
    old_router = re.search(r'(router\s*=\s*APIRouter\()([^)]*?)(\))', content)
    if old_router and "dependencies" not in old_router.group(0):
        args = old_router.group(2).strip()
        if args:
            new_router = f'{old_router.group(1)}{args}, dependencies=[Depends(get_current_user)]{old_router.group(3)}'
        else:
            new_router = f'{old_router.group(1)}dependencies=[Depends(get_current_user)]{old_router.group(3)}'
        content = content.replace(old_router.group(0), new_router)

    filepath.write_text(content)
    print(f"  ✅ Fixed {filepath.name}")


def main():
    print("=== BrAPI Aggregator Routers ===")
    fix_brapi_routers()

    print("\n=== v2 Files with partial auth ===")
    # Files that have auth on some endpoints but not all — add router-level guard
    partial_auth_files = [
        "social.py",        # feed, groups, trending, reputation — no auth at all
        "chat.py",          # /health, /status unprotected
        "devguru.py",       # milestone_statuses, phases, projects, etc. unprotected
        "dus.py",           # crops, reference endpoints unprotected
        "genotyping.py",    # several endpoints unprotected
        "pedigree.py",      # /individuals unprotected
        "team_management.py",  # teams, invites, roles, etc. unprotected
        "vision.py",        # base_models, crops unprotected
        "crossing_planner.py",  # reference endpoints unprotected
        "barcode.py",       # entity_types reference unprotected
        "integrations.py",  # /available unprotected
    ]

    v2_dir = BASE / "app" / "api" / "v2"
    for fname in partial_auth_files:
        fpath = v2_dir / fname
        if fpath.exists():
            add_router_deps(fpath)
        else:
            print(f"  ⚠️  {fname} not found")


if __name__ == "__main__":
    main()
