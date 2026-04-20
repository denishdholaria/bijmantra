"""
Spatial Domain API Router

Consolidates all spatial-related endpoints under /api/v2/spatial/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Spatial Analysis (GIS queries, zonal statistics, point extraction)
- Field Mapping (field and plot spatial data, location queries)
- Yield Mapping (spatial visualization of yield data)
"""

from fastapi import APIRouter

# Import all spatial-related routers
from app.api.v2 import (
    field_map,
    spatial,
    yield_map,
)

# Create main spatial router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Spatial"])

# Include all spatial sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(spatial.router, prefix="/spatial", tags=["Spatial Analysis"])
router.include_router(field_map.router, tags=["Field Map"])
router.include_router(yield_map.router, tags=["Yield Map"])
