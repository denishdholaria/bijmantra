"""
Germplasm Domain API Router

Consolidates all germplasm-related endpoints under /api/v2/germplasm/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Germplasm Collections (collection management, statistics)
- Germplasm Comparison (trait and marker comparison)
- Germplasm Search (advanced search and discovery)
- Passport Data (MCPD-compliant passport descriptors)
- Pedigree Analysis (relationship matrices, ancestry tracing)
"""

from fastapi import APIRouter

# Import all germplasm-related routers
from app.api.v2 import (
    germplasm_collection,
    germplasm_comparison,
    germplasm_search,
    passport,
    pedigree,
)

# Create main germplasm router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Germplasm"])

# Include all germplasm sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(germplasm_collection.router, tags=["Germplasm Collections"])
router.include_router(germplasm_comparison.router, tags=["Germplasm Comparison"])
router.include_router(germplasm_search.router, tags=["Germplasm Search"])
router.include_router(passport.router, tags=["Germplasm Passport"])
router.include_router(pedigree.router, tags=["Pedigree Analysis"])
