"""
BrAPI v2.1 Router Aggregator (Interop Domain)

Consolidates all BrAPI v2.1 endpoints under /brapi/v2/*
This is the central router for all Breeding API standard endpoints.

BrAPI Modules:
- Core: Programs, Locations, Trials, Studies, Seasons
- Germplasm: Germplasm, Crosses, Seed Lots, Attributes
- Phenotyping: Observations, Observation Units, Traits, Variables, Methods, Scales, Ontologies
- Genotyping: Variants, Calls, CallSets, Plates, References, Maps, Allele Matrix
- Extensions: IoT (custom extension)

This router is part of the Interop domain as BrAPI is an interoperability standard
for plant breeding data exchange.
"""

from fastapi import APIRouter, Depends

# Import all BrAPI routers
from app.api.brapi import (
    allelematrix,
    attributes,
    attributevalues,
    breedingmethods,
    calls,
    callsets,
    crosses,
    crossingprojects,
    events,
    germplasm,
    images,
    maps,
    markerpositions,
    methods,
    observationlevels,
    observations,
    observationunits,
    ontologies,
    people,
    plannedcrosses,
    plates,
    references,
    referencesets,
    samples,
    scales,
    search,
    seedlots,
    traits,
    variables,
    variants,
    variantsets,
    vendor,
)
from app.api.brapi.extensions import iot as brapi_iot
from app.api.deps import get_current_user

# Create main BrAPI router
# This router will be mounted at /brapi/v2 in main.py
brapi_router = APIRouter(tags=["BrAPI v2.1"], dependencies=[Depends(get_current_user)])

# ============================================
# BrAPI Germplasm Endpoints
# ============================================
brapi_router.include_router(germplasm.router, tags=["BrAPI Germplasm"])
brapi_router.include_router(crosses.router, tags=["BrAPI Germplasm - Crosses"])
brapi_router.include_router(seedlots.router, tags=["BrAPI Germplasm - Seed Lots"])
brapi_router.include_router(attributes.router, tags=["BrAPI Germplasm - Attributes"])
brapi_router.include_router(attributevalues.router, tags=["BrAPI Germplasm - Attribute Values"])
brapi_router.include_router(breedingmethods.router, tags=["BrAPI Germplasm - Breeding Methods"])
brapi_router.include_router(crossingprojects.router, tags=["BrAPI Germplasm - Crossing Projects"])
brapi_router.include_router(plannedcrosses.router, tags=["BrAPI Germplasm - Planned Crosses"])

# ============================================
# BrAPI Phenotyping Endpoints
# ============================================
brapi_router.include_router(traits.router, tags=["BrAPI Phenotyping - Traits"])
brapi_router.include_router(variables.router, tags=["BrAPI Phenotyping - Variables"])
brapi_router.include_router(observations.router, tags=["BrAPI Phenotyping - Observations"])
brapi_router.include_router(observationunits.router, tags=["BrAPI Phenotyping - Observation Units"])
brapi_router.include_router(events.router, tags=["BrAPI Phenotyping - Events"])
brapi_router.include_router(methods.router, tags=["BrAPI Phenotyping - Methods"])
brapi_router.include_router(scales.router, tags=["BrAPI Phenotyping - Scales"])
brapi_router.include_router(ontologies.router, tags=["BrAPI Phenotyping - Ontologies"])
brapi_router.include_router(observationlevels.router, tags=["BrAPI Phenotyping - Observation Levels"])
brapi_router.include_router(images.router, tags=["BrAPI Phenotyping - Images"])
brapi_router.include_router(samples.router, tags=["BrAPI Phenotyping - Samples"])

# ============================================
# BrAPI Genotyping Endpoints
# ============================================
brapi_router.include_router(calls.router, tags=["BrAPI Genotyping - Calls"])
brapi_router.include_router(callsets.router, tags=["BrAPI Genotyping - CallSets"])
brapi_router.include_router(variants.router, tags=["BrAPI Genotyping - Variants"])
brapi_router.include_router(variantsets.router, tags=["BrAPI Genotyping - VariantSets"])
brapi_router.include_router(plates.router, tags=["BrAPI Genotyping - Plates"])
brapi_router.include_router(references.router, tags=["BrAPI Genotyping - References"])
brapi_router.include_router(referencesets.router, tags=["BrAPI Genotyping - ReferenceSets"])
brapi_router.include_router(maps.router, tags=["BrAPI Genotyping - Maps"])
brapi_router.include_router(markerpositions.router, tags=["BrAPI Genotyping - Marker Positions"])
brapi_router.include_router(allelematrix.router, tags=["BrAPI Genotyping - Allele Matrix"])
brapi_router.include_router(vendor.router, tags=["BrAPI Genotyping - Vendor"])

# ============================================
# BrAPI Search & Utility Endpoints
# ============================================
brapi_router.include_router(search.router, tags=["BrAPI Search"])
brapi_router.include_router(people.router, tags=["BrAPI People"])

# ============================================
# BrAPI Extensions
# ============================================
brapi_router.include_router(brapi_iot.router, tags=["BrAPI IoT Extension"])
