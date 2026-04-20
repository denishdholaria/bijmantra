"""
Interop Domain API Router

Consolidates all interoperability and external integration endpoints under /api/v2/interop/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- Integration Hub (External API integrations: NCBI, Earth Engine, OpenWeatherMap, ERPNext, Webhooks)
- GRIN-Global (USDA Germplasm Resources Information Network)
- Genesys (Global portal for plant genetic resources)
- BrAPI (Breeding API v2.1 standard endpoints)
"""

from fastapi import APIRouter

# Import all interop-related routers
from app.api.v2 import (
    integrations,
    grin,
)

# Create main interop router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Interop"])

# Include all interop sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(integrations.router, tags=["Integration Hub"])
router.include_router(grin.router, tags=["GRIN-Global Integration"])
