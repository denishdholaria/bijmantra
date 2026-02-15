"""
BrAPI Genotyping Router Aggregator
Combines all BrAPI v2.1 Genotyping endpoints into a single router.
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

from app.api.brapi import (
    calls,
    callsets,
    variants,
    variantsets,
    plates,
    references,
    referencesets,
    maps,
    markerpositions,
    allelematrix,
    search,
    vendor,
)

brapi_genotyping_router = APIRouter(tags=["BrAPI Genotyping"], dependencies=[Depends(get_current_user)])

# Genotyping Endpoints
brapi_genotyping_router.include_router(calls.router, tags=["Genotyping - Calls"])
brapi_genotyping_router.include_router(callsets.router, tags=["Genotyping - CallSets"])
brapi_genotyping_router.include_router(variants.router, tags=["Genotyping - Variants"])
brapi_genotyping_router.include_router(variantsets.router, tags=["Genotyping - VariantSets"])
brapi_genotyping_router.include_router(plates.router, tags=["Genotyping - Plates"])
brapi_genotyping_router.include_router(references.router, tags=["Genotyping - References"])
brapi_genotyping_router.include_router(referencesets.router, tags=["Genotyping - ReferenceSets"])
brapi_genotyping_router.include_router(maps.router, tags=["Genotyping - Maps"])
brapi_genotyping_router.include_router(markerpositions.router, tags=["Genotyping - Marker Positions"])
brapi_genotyping_router.include_router(allelematrix.router, tags=["Genotyping - Allele Matrix"])
brapi_genotyping_router.include_router(search.router, tags=["BrAPI Search"])
brapi_genotyping_router.include_router(vendor.router, tags=["Genotyping - Vendor"])
