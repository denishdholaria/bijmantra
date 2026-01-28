"""
BrAPI Germplasm & Phenotyping Router Aggregator
Combines all BrAPI v2.1 Germplasm and Phenotyping endpoints into a single router.
"""
from fastapi import APIRouter

from app.api.brapi import (
    germplasm,
    crosses,
    traits,
    variables,
    observations,
    observationunits,
    events,
    images,
    samples,
    seedlots,
    people,
    attributes,
    attributevalues,
    breedingmethods,
    crossingprojects,
    plannedcrosses,
    methods,
    scales,
    ontologies,
    observationlevels,
)
from app.api.brapi.extensions import iot as brapi_iot

brapi_germplasm_router = APIRouter(tags=["BrAPI Germplasm"])

# Germplasm Endpoints
brapi_germplasm_router.include_router(germplasm.router, tags=["Germplasm"])
brapi_germplasm_router.include_router(crosses.router, tags=["Crosses"])
brapi_germplasm_router.include_router(traits.router, tags=["Traits"])
brapi_germplasm_router.include_router(variables.router, tags=["Observation Variables"])
brapi_germplasm_router.include_router(observations.router, tags=["Observations"])
brapi_germplasm_router.include_router(observationunits.router, tags=["Observation Units"])
brapi_germplasm_router.include_router(events.router, tags=["Events"])
brapi_germplasm_router.include_router(images.router, tags=["Images"])
brapi_germplasm_router.include_router(samples.router, tags=["Samples"])
brapi_germplasm_router.include_router(seedlots.router, tags=["Seed Lots"])
brapi_germplasm_router.include_router(people.router, tags=["People"])
brapi_germplasm_router.include_router(attributes.router, tags=["Germplasm Attributes"])
brapi_germplasm_router.include_router(attributevalues.router, tags=["Germplasm Attribute Values"])
brapi_germplasm_router.include_router(breedingmethods.router, tags=["Breeding Methods"])
brapi_germplasm_router.include_router(crossingprojects.router, tags=["Crossing Projects"])
brapi_germplasm_router.include_router(plannedcrosses.router, tags=["Planned Crosses"])

# Phenotyping Endpoints
brapi_germplasm_router.include_router(methods.router, tags=["Methods"])
brapi_germplasm_router.include_router(scales.router, tags=["Scales"])
brapi_germplasm_router.include_router(ontologies.router, tags=["Ontologies"])
brapi_germplasm_router.include_router(observationlevels.router, tags=["Observation Levels"])

# Extensions
brapi_germplasm_router.include_router(brapi_iot.router, tags=["BrAPI IoT Extension"])
