"""
Phenotyping Domain API Router

Consolidates all phenotyping-related endpoints under /api/v2/phenotyping/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Phenotype Analysis (statistical analysis, heritability, ANOVA)
- Phenology Tracking (growth stages, development)
- Phenomic Selection (high-throughput phenotyping, spectral data)
- Phenotype Comparison (germplasm comparison)
- Image Analysis (spectral indices, computer vision)
"""

from fastapi import APIRouter

# Import all phenotyping-related routers
from app.api.v2 import (
    phenotype,
    phenology,
    phenomic_selection,
    phenotype_comparison,
    image_analysis,
)

# Create main phenotyping router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Phenotyping"])

# Include all phenotyping sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(phenotype.router, tags=["Phenotype Analysis"])
router.include_router(phenology.router, tags=["Phenology Tracker"])
router.include_router(phenomic_selection.router, tags=["Phenomic Selection"])
router.include_router(phenotype_comparison.router, tags=["Phenotype Comparison"])
router.include_router(image_analysis.router, tags=["Image Analysis"])
