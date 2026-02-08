"""
Plant Sciences Module - Main Router

Aggregates all sub-routers for the Plant Sciences division.
"""

from fastapi import APIRouter

# Import sub-routers
from .breeding.routes import router as breeding_router
from .genomics.routes import router as genomics_router
from .phenotyping.routes import router as phenotyping_router
from .genotyping.routes import router as genotyping_router

# Main router for Plant Sciences module
router = APIRouter(prefix="/plant-sciences", tags=["Plant Sciences"])

# Mount sub-routers
router.include_router(breeding_router, prefix="/breeding", tags=["Breeding"])
router.include_router(genomics_router, prefix="/genomics", tags=["Genomics"])
router.include_router(phenotyping_router, prefix="/phenotyping", tags=["Phenotyping"])
router.include_router(genotyping_router, prefix="/genotyping", tags=["Genotyping"])


@router.get("/")
async def plant_sciences_overview():
    """Get Plant Sciences division overview."""
    return {
        "division": "plant-sciences",
        "name": "Plant Sciences",
        "status": "active",
        "subsections": [
            {"id": "breeding", "name": "Breeding Operations"},
            {"id": "genomics", "name": "Genetics & Genomics"},
            {"id": "phenotyping", "name": "Phenotyping"},
            {"id": "genotyping", "name": "Genotyping"},
        ],
    }
