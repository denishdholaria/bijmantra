"""
Route registration for Bijmantra API.

This module centralizes all router includes following domain organization.

Routing architecture (single path):
  register_auth_routes  → /api/auth/*
  register_brapi_routes → /brapi/v2/*  (BrAPI v2.1 standard)
  register_product_routes → /api/v2/*  (all product endpoints via apex_router)

The apex_router aggregates every domain package under /api/v2.
There is intentionally only ONE product router registration path to avoid
duplicate route entries in the OpenAPI schema.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register_auth_routes(app: FastAPI):
    """Register core authentication routes."""
    from app.api import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])


def register_brapi_routes(app: FastAPI):
    """Register BrAPI v2.1 interoperability routes."""
    from app.api.brapi.v2.router import brapi_v2_router
    app.include_router(brapi_v2_router, prefix="/brapi/v2")


def register_product_routes(app: FastAPI):
    """
    Register all BijMantra product API routes via apex_router.

    The apex_router is the single aggregation point for all domain packages:
    AI, Breeding, Collaboration, Compute, Control Plane, Data, Developer,
    Environment, Field, Future, Genomics, Germplasm, Inventory, IoT,
    Monitoring, Operations, Phenotyping, Research, Security, System, Trials.

    Do NOT add a second registration path here. All new domains belong in
    apex_router.py.
    """
    from app.api.bijmantra.apex_router import apex_router
    app.include_router(apex_router, prefix="/api/v2")


def register_all_routes(app: FastAPI):
    """
    Register all application routes.

    Single-path routing: auth → brapi → product (apex_router).
    """
    logger.info("Registering routes...")
    register_auth_routes(app)
    register_brapi_routes(app)
    register_product_routes(app)
    logger.info("All routes registered successfully")
