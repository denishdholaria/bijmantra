"""
APEX Router Aggregator
Combines all Bijmantra-specific API endpoints (non-BrAPI).
This is the largest router, aggregating 80+ modules.
"""
from fastapi import APIRouter

from app.api.bijmantra.ai.router import ai_router
from app.api.bijmantra.breeding.router import breeding_router
from app.api.bijmantra.collaboration.router import collaboration_router
from app.api.bijmantra.compute.router import compute_router
from app.api.bijmantra.control_plane.router import control_plane_router
from app.api.bijmantra.data.router import data_router

# ============================================================================
# APEX Core Imports
# ============================================================================
from app.api.bijmantra.developer.router import developer_router
from app.api.bijmantra.environment.router import environment_router
from app.api.bijmantra.field.router import field_router
from app.api.bijmantra.future.router import future_router
from app.api.bijmantra.genomics.router import genomics_router
from app.api.bijmantra.germplasm.router import germplasm_router
from app.api.bijmantra.inventory.router import inventory_router
from app.api.bijmantra.iot.router import iot_router
from app.api.bijmantra.monitoring.router import monitoring_router
from app.api.bijmantra.operations.router import operations_router
from app.api.bijmantra.phenotyping.router import phenotyping_router
from app.api.bijmantra.research.router import research_router
from app.api.bijmantra.security.router import security_router
from app.api.bijmantra.system.router import system_router
from app.api.bijmantra.trials.router import trials_router
from app.domains.germplasm.capabilities.accession_passport.adapters.api.mcpd import (
    router as seed_bank_mcpd_router,
)
from app.modules.bio_analytics.router import router as bio_analytics_router
from app.modules.core.router import router as core_module_router
from app.modules.crop_calendar.router import router as crop_calendar_module_router

# Module routers that own real routes not covered by api/bijmantra/*
from app.modules.seed_bank.router import router as seed_bank_module_router
from app.modules.weather.router import router as weather_module_router


apex_router = APIRouter(tags=["APEX"])

# ============================================================================
# AI & Analytics
# ============================================================================
apex_router.include_router(ai_router, tags=["AI"])
apex_router.include_router(compute_router, tags=["Compute"])
apex_router.include_router(developer_router, tags=["Developer"])
apex_router.include_router(bio_analytics_router, prefix="/bio-analytics", tags=["Bio-Analytics"])
apex_router.include_router(weather_module_router, tags=["Weather Service"])

# ============================================================================
# Weather & Climate
# ============================================================================
apex_router.include_router(environment_router, tags=["Environment"])

# ============================================================================
# Breeding & Genetics
# ============================================================================
apex_router.include_router(germplasm_router, tags=["Germplasm"])
apex_router.include_router(breeding_router, tags=["Breeding"])
apex_router.include_router(genomics_router, tags=["Genomics"])
apex_router.include_router(phenotyping_router, tags=["Phenotyping"])

# ============================================================================
# Trials & Field
# ============================================================================
apex_router.include_router(trials_router, tags=["Trials"])

# Field domain package
apex_router.include_router(field_router, tags=["Field"])

# ============================================================================
# Seed & Inventory
# ============================================================================
apex_router.include_router(inventory_router, tags=["Inventory"])

# ============================================================================
# Research & Analysis
# ============================================================================
apex_router.include_router(research_router, tags=["Research"])

# ============================================================================
# Data & Quality
# ============================================================================
apex_router.include_router(data_router, tags=["Data"])

# ============================================================================
# Operations & Integrations
# ============================================================================
apex_router.include_router(operations_router, tags=["Operations"])

# ============================================================================
# Collaboration & Team
# ============================================================================
apex_router.include_router(collaboration_router, tags=["Collaboration"])

# ============================================================================
# System & Security
# ============================================================================
apex_router.include_router(system_router, tags=["System"])
apex_router.include_router(monitoring_router, tags=["Monitoring"])
apex_router.include_router(security_router, tags=["Security"])

# ============================================================================
# Control Plane & IoT
# ============================================================================
apex_router.include_router(control_plane_router, tags=["Control Plane"])
apex_router.include_router(iot_router, tags=["IoT"])

# ============================================================================
# Future / Earth Systems
# ============================================================================
apex_router.include_router(future_router, prefix="/future", tags=["Future"])

# ============================================================================
# Module-owned routes (not covered by api/bijmantra/* packages)
# These routers live in app/modules/ and own their own endpoints directly.
# ============================================================================
apex_router.include_router(seed_bank_module_router, tags=["Seed Bank"])
apex_router.include_router(
    seed_bank_mcpd_router,
    prefix="/seed-bank",
    tags=["Seed Bank MCPD"],
)
apex_router.include_router(crop_calendar_module_router, tags=["Crop Calendar"])
apex_router.include_router(core_module_router, tags=["Core Domain"])

# NOTE: app.modules.soil.router is intentionally not mounted here yet. That module
# currently has no organization_id model boundary, no tenant DB dependency, and no
# auth dependency. Mounting it at the canonical /api/v2/soil path would turn route
# cleanup into an unauthenticated tenant-isolation bypass.
