"""
BrAPI v2.1 Unified Router Aggregator
Combines all BrAPI v2.1 endpoints (Core, Germplasm, Phenotyping, Genotyping, Extensions) into a single router.
"""
from fastapi import APIRouter, Depends

# Core endpoints
from app.api.brapi.v2.core import (
    commoncropnames,
    lists,
    locations,
    pedigree,
    programs,
    seasons,
    serverinfo,
    studies,
    studytypes,
    trials,
)

# Germplasm, Phenotyping, and Genotyping endpoints
from app.api.brapi.v2 import (
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
    markers,
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

# Extensions
from app.api.brapi.v2.extensions import iot as brapi_iot

from app.api.deps import get_current_user


brapi_v2_router = APIRouter(tags=["BrAPI v2.1"], dependencies=[Depends(get_current_user)])

# ─── Core Endpoints ───
brapi_v2_router.include_router(programs.router, tags=["Core - Programs"])
brapi_v2_router.include_router(locations.router, tags=["Core - Locations"])
brapi_v2_router.include_router(trials.router, tags=["Core - Trials"])
brapi_v2_router.include_router(studies.router, tags=["Core - Studies"])
brapi_v2_router.include_router(seasons.router, tags=["Core - Seasons"])
brapi_v2_router.include_router(serverinfo.router, tags=["Core - Server Info"])
brapi_v2_router.include_router(commoncropnames.router, tags=["Core - Common Crop Names"])
brapi_v2_router.include_router(lists.router, tags=["Core - Lists"])
brapi_v2_router.include_router(studytypes.router, tags=["Core - Study Types"])
brapi_v2_router.include_router(pedigree.router, tags=["Core - Pedigree"])

# ─── Germplasm Endpoints ───
brapi_v2_router.include_router(germplasm.router, tags=["Germplasm"])
brapi_v2_router.include_router(crosses.router, tags=["Crosses"])
brapi_v2_router.include_router(seedlots.router, tags=["Seed Lots"])
brapi_v2_router.include_router(people.router, tags=["People"])
brapi_v2_router.include_router(attributes.router, tags=["Germplasm Attributes"])
brapi_v2_router.include_router(attributevalues.router, tags=["Germplasm Attribute Values"])
brapi_v2_router.include_router(breedingmethods.router, tags=["Breeding Methods"])
brapi_v2_router.include_router(crossingprojects.router, tags=["Crossing Projects"])
brapi_v2_router.include_router(plannedcrosses.router, tags=["Planned Crosses"])

# ─── Phenotyping Endpoints ───
brapi_v2_router.include_router(traits.router, tags=["Traits"])
brapi_v2_router.include_router(variables.router, tags=["Observation Variables"])
brapi_v2_router.include_router(observations.router, tags=["Observations"])
brapi_v2_router.include_router(observationunits.router, tags=["Observation Units"])
brapi_v2_router.include_router(events.router, tags=["Events"])
brapi_v2_router.include_router(images.router, tags=["Images"])
brapi_v2_router.include_router(samples.router, tags=["Samples"])
brapi_v2_router.include_router(methods.router, tags=["Methods"])
brapi_v2_router.include_router(scales.router, tags=["Scales"])
brapi_v2_router.include_router(ontologies.router, tags=["Ontologies"])
brapi_v2_router.include_router(observationlevels.router, tags=["Observation Levels"])

# ─── Genotyping Endpoints ───
brapi_v2_router.include_router(calls.router, tags=["Genotyping - Calls"])
brapi_v2_router.include_router(callsets.router, tags=["Genotyping - CallSets"])
brapi_v2_router.include_router(variants.router, tags=["Genotyping - Variants"])
brapi_v2_router.include_router(variantsets.router, tags=["Genotyping - VariantSets"])
brapi_v2_router.include_router(plates.router, tags=["Genotyping - Plates"])
brapi_v2_router.include_router(references.router, tags=["Genotyping - References"])
brapi_v2_router.include_router(referencesets.router, tags=["Genotyping - ReferenceSets"])
brapi_v2_router.include_router(maps.router, tags=["Genotyping - Maps"])
brapi_v2_router.include_router(markers.router, tags=["Genotyping - Markers"])
brapi_v2_router.include_router(markerpositions.router, tags=["Genotyping - Marker Positions"])
brapi_v2_router.include_router(allelematrix.router, tags=["Genotyping - Allele Matrix"])
brapi_v2_router.include_router(search.router, tags=["BrAPI Search"])
brapi_v2_router.include_router(vendor.router, tags=["Genotyping - Vendor"])

# ─── Extensions ───
brapi_v2_router.include_router(brapi_iot.router, tags=["BrAPI IoT Extension"])
