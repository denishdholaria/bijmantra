"""
Germplasm domain router aggregator.

This module aggregates all germplasm-related routers into a single router
for mounting in the apex router.
"""

from fastapi import APIRouter

from app.api.bijmantra.germplasm import (
    genetic_diversity,
    genetic_gain,
    germplasm_collection,
    germplasm_comparison,
    germplasm_search,
    grin,
    passport,
    pedigree,
)

germplasm_router = APIRouter()

# Include all germplasm domain routers
germplasm_router.include_router(genetic_diversity.router, tags=["Genetic Diversity"])
germplasm_router.include_router(genetic_gain.router, tags=["Genetic Gain"])
germplasm_router.include_router(germplasm_collection.router, tags=["Germplasm Collections"])
germplasm_router.include_router(germplasm_comparison.router, tags=["Germplasm Comparison"])
germplasm_router.include_router(germplasm_search.router, tags=["Germplasm Search"])
germplasm_router.include_router(grin.router, tags=["GRIN-Global Integration"])
germplasm_router.include_router(passport.router, tags=["Germplasm Passport"])
germplasm_router.include_router(pedigree.router, tags=["Pedigree Analysis"])
