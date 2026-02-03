"""
BrAPI Core Router Aggregator
Combines all BrAPI v2.1 Core endpoints into a single router.
"""
from fastapi import APIRouter

from app.api.v2.core import (
    programs,
    locations,
    trials,
    studies,
    seasons,
    serverinfo,
    commoncropnames,
    lists,
    studytypes,
    pedigree,
)

brapi_core_router = APIRouter(tags=["BrAPI Core"])

# Core Endpoints
brapi_core_router.include_router(programs.router, tags=["Core - Programs"])
brapi_core_router.include_router(locations.router, tags=["Core - Locations"])
brapi_core_router.include_router(trials.router, tags=["Core - Trials"])
brapi_core_router.include_router(studies.router, tags=["Core - Studies"])
brapi_core_router.include_router(seasons.router, tags=["Core - Seasons"])
brapi_core_router.include_router(serverinfo.router, tags=["Core - Server Info"])
brapi_core_router.include_router(commoncropnames.router, tags=["Core - Common Crop Names"])
brapi_core_router.include_router(lists.router, tags=["Core - Lists"])
brapi_core_router.include_router(studytypes.router, tags=["Core - Study Types"])
brapi_core_router.include_router(pedigree.router, tags=["Core - Pedigree"])
