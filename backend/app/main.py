"""
Bijmantra - BrAPI v2.1 Plant Breeding Application
FastAPI Backend with Real-time Collaboration

This is the refactored main.py using Domain Router Aggregators.
See: app/api/v2/core/router.py, app/api/brapi/router.py, etc.
"""

import asyncio
import json
import logging
import os
import secrets
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from hashlib import sha256
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from starlette.responses import Response as StarletteResponse

from app.core.config import settings


logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=os.getenv('ENVIRONMENT', 'development'),
    )

# Lifespan for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Bijmantra API...")

    # Initialize Redis for ephemeral data (jobs, search cache)
    try:
        from app.core.redis import redis_client
        connected = await redis_client.connect()
        if connected:
            logger.info("Redis connected for job/cache storage")
        else:
            logger.warning("Redis using in-memory fallback (not recommended for production)")
    except Exception as e:
        logger.warning("Redis initialization skipped: %s", e)

    # Initialize Meilisearch
    try:
        from app.core.meilisearch import meilisearch_service
        if meilisearch_service.connect():
            meilisearch_service.setup_indexes()
    except Exception as e:
        logger.warning("Meilisearch initialization skipped: %s", e)

    # Start background task queue
    try:
        from app.services.task_queue import task_queue
        await task_queue.start()
    except Exception as e:
        logger.warning("TaskQueue initialization skipped: %s", e)

    # Initialize Redis security storage
    try:
        from app.services.redis_security import init_redis_security
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            await init_redis_security(redis_url)
            logger.info("Redis security storage initialized")
        else:
            logger.warning("No REDIS_URL configured, using in-memory storage for security")
    except Exception as e:
        logger.warning("Redis security storage initialization skipped: %s", e)

    yield

    # Shutdown
    logger.info("Shutting down Bijmantra API...")

    # Disconnect Redis
    try:
        from app.core.redis import redis_client
        await redis_client.disconnect()
    except Exception:
        pass

    # Stop task queue
    try:
        from app.services.task_queue import task_queue
        await task_queue.stop()
    except Exception:
        pass

# Create FastAPI app
app = FastAPI(
    title="Bijmantra API",
    description="BrAPI v2.1 compatible Plant Breeding Application with Real-time Collaboration",
    version=settings.APP_VERSION,
    docs_url=None,  # Disabled for custom override with nonce
    redoc_url=None,  # Disabled for custom override with nonce
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware - Restricted methods (M1 security fix)
# Only allow methods actually used by the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Function middleware is used here to avoid BaseHTTPMiddleware overhead."""
    # Generate nonce for CSP
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Dynamic CSP Policy based on path
    # API endpoints use a strict policy, while docs use a nonce-based policy
    path = request.url.path
    if path.startswith(("/docs", "/redoc")):
        # Relaxed policy for documentation - allow CDN and nonced inline scripts
        # We also allow unsafe-inline for styles as Swagger/ReDoc rely heavily on them
        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            f"img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            f"font-src 'self' data: https://cdn.jsdelivr.net; "
            f"connect-src 'self';"
        )
    else:
        # Strict policy for API and other endpoints (No unsafe-inline or unsafe-eval)
        csp_policy = (
            "default-src 'none'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self';"
        )

    response.headers["Content-Security-Policy"] = csp_policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )

    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


STATIC_BRAPI_CACHE_PATHS = {"/brapi/v2/serverinfo"}


@app.middleware("http")
async def brapi_static_cache_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Adds lightweight ETag + Cache-Control handling for static BrAPI responses."""
    response = await call_next(request)

    if request.method != "GET" or request.url.path not in STATIC_BRAPI_CACHE_PATHS or response.status_code != 200:
        return response

    # Skip if upstream already set validators.
    if "etag" in response.headers:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    etag = f'W/"{sha256(body).hexdigest()}"'
    if request.headers.get("if-none-match") == etag:
        return StarletteResponse(status_code=304, headers={"ETag": etag, "Cache-Control": "public, max-age=300"})

    headers = dict(response.headers)
    headers["ETag"] = etag
    headers["Cache-Control"] = "public, max-age=300"

    return StarletteResponse(content=body, status_code=response.status_code, headers=headers, media_type=response.media_type)

logger.info("Security headers middleware enabled")

# Audit middleware (non-blocking inserts + emergency lockdown gate)
try:
    from app.middleware.audit_middleware import AuditMiddleware
    app.add_middleware(AuditMiddleware)
    logger.info("Audit middleware enabled")
except Exception as e:
    logger.warning("Audit middleware not available: %s", e)

if os.getenv("ENVIRONMENT", "development") == "development":
    try:
        from app.middleware.route_profiler import RouteProfilerMiddleware

        app.add_middleware(RouteProfilerMiddleware)
        logger.info("Route profiler middleware enabled")
    except Exception as e:
        logger.warning("Route profiler unavailable: %s", e)

# Security middleware (PRAHARI integration)
try:
    from app.middleware.security import SecurityMiddleware
    app.add_middleware(SecurityMiddleware, enabled=True)
    logger.info("Security middleware enabled")
except Exception as e:
    logger.warning("Security middleware not available: %s", e)

# Tenant context middleware (RLS support)
try:
    from app.middleware.tenant_context import TenantContextMiddleware
    app.add_middleware(TenantContextMiddleware)
    logger.info("Tenant context middleware enabled")
except Exception as e:
    logger.warning("Tenant context middleware not available: %s", e)

# Mount Socket.IO
try:
    from app.core.socketio import socket_app
    app.mount("/ws", socket_app)
    logger.info("Socket.IO mounted at /ws")
except Exception as e:
    logger.warning("Socket.IO not available: %s", e)

# =============================================================================
# DOCUMENTATION ROUTES WITH CSP NONCE
# =============================================================================


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """Custom Swagger UI handler that injects CSP nonce."""
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url

    nonce = getattr(request.state, "csp_nonce", "")

    response = get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

    # Inject nonce into script tags
    content = response.body.decode()
    content = content.replace("<script>", f'<script nonce="{nonce}">')
    content = content.replace('<script src="', f'<script nonce="{nonce}" src="')

    return HTMLResponse(content=content)


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect(request: Request):
    """Custom Swagger UI OAuth2 redirect handler that injects CSP nonce."""
    nonce = getattr(request.state, "csp_nonce", "")
    response = get_swagger_ui_oauth2_redirect_html()

    # Inject nonce into script tags
    content = response.body.decode()
    content = content.replace("<script>", f'<script nonce="{nonce}">')

    return HTMLResponse(content=content)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html(request: Request):
    """Custom ReDoc handler that injects CSP nonce."""
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    nonce = getattr(request.state, "csp_nonce", "")

    response = get_redoc_html(
        openapi_url=openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

    # Inject nonce into script tags
    content = response.body.decode()
    content = content.replace("<script>", f'<script nonce="{nonce}">')
    content = content.replace('<script src="', f'<script nonce="{nonce}" src="')

    return HTMLResponse(content=content)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Bijmantra API",
        "version": settings.APP_VERSION,
        "brapi_version": settings.BRAPI_VERSION,
        "docs": "/docs",
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

def _load_metrics_sync(path: Path) -> int:
    """Helper to load metrics synchronously for offloading to thread"""
    with open(path) as f:
        metrics = json.load(f)
        return metrics.get("api", {}).get("totalEndpoints", 1370)


# API Statistics
@app.get("/api/stats")
async def api_stats():
    """API statistics and version info - reads from metrics.json with failsafe"""
    # Try multiple locations for failsafe
    metrics_paths = [
        Path(__file__).parent.parent / "metrics.json",  # /metrics.json (root)
        Path(__file__).parent.parent / ".kiro" / "metrics.json",  # /.kiro/metrics.json (legacy)
    ]

    total_endpoints = 1370  # Failsafe default

    for metrics_path in metrics_paths:
        if metrics_path.exists():
            try:
                # Offload blocking I/O and JSON parsing to a thread
                total_endpoints = await asyncio.to_thread(_load_metrics_sync, metrics_path)
                break
            except (OSError, json.JSONDecodeError):
                continue

    return {
        "name": "Bijmantra API",
        "version": settings.APP_VERSION,
        "brapi_version": settings.BRAPI_VERSION,
        "total_endpoints": total_endpoints,
        "modules": [
            "Authentication", "BrAPI Core", "BrAPI IoT Extension", "Compute Engine", "AI Insights",
            "Vector Store", "Weather", "Veena AI", "Cross Prediction",
            "Integration Hub", "Event Bus", "Task Queue", "Field Environment",
            "Voice", "G×E Analysis", "GWAS", "Bioinformatics", "Pedigree",
            "Phenotype", "MAS", "Trial Design", "Seed Inventory", "Crop Calendar",
            "Data Export", "Quality Control", "Germplasm Passport", "Trait Ontology",
            "Nursery Management", "Seed Traceability", "Variety Licensing",
            "Selection Index", "Genetic Gain", "Harvest Management", "Resource Management",
            "Spatial Analysis", "Breeding Value", "Disease Resistance", "Abiotic Stress",
            "Dispatch Management", "Seed Processing", "Sensor Networks", "Community Forums",
            "Sun-Earth Systems", "Space Research", "Vision Training Ground",
            "RAKSHAKA Self-Healing", "PRAHARI Defense", "CHAITANYA Orchestrator", "Security Audit",
            "DevGuru PhD Mentor"
        ],
        "status": "operational",
    }

# BrAPI v2.1 serverinfo endpoint
@app.get("/brapi/v2/serverinfo")
async def serverinfo():
    """BrAPI serverinfo endpoint"""
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}],
        },
        "result": {
            "calls": [],
            "contactEmail": "hello@bijmantra.org",
            "documentationURL": "https://github.com/yourusername/bijmantra",
            "location": "India",
            "organizationName": "Bijmantra",
            "organizationURL": "https://gitlab.com/denishdholaria/bijmantraorg",
            "serverDescription": "Bijmantra - Plant Breeding Application",
            "serverName": "Bijmantra",
        },
    }

# =============================================================================
# DOMAIN ROUTER AGGREGATORS
# =============================================================================
# These aggregators combine all routers into cohesive domains.
# This reduces main.py from 621 lines to ~280 lines.
# =============================================================================

# Auth
from app.api import auth


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

from app.api.v1.endpoints import pedigree as pedigree_v1


app.include_router(pedigree_v1.router, prefix="/api/v1")

# BrAPI Core (Programs, Locations, Trials, Studies, Seasons, etc.)
from app.api.v2.core.router import brapi_core_router


app.include_router(brapi_core_router, prefix="/brapi/v2")

# BrAPI Germplasm & Phenotyping
from app.api.brapi.router import brapi_germplasm_router


app.include_router(brapi_germplasm_router, prefix="/brapi/v2")

# BrAPI Genotyping
from app.api.brapi.genotyping_router import brapi_genotyping_router


app.include_router(brapi_genotyping_router, prefix="/brapi/v2")

# APEX (Bijmantra-specific APIs: Weather, AI, GxE, etc.)
from app.api.v2.apex_router import apex_router


app.include_router(apex_router, prefix="/api/v2")

# Future / Earth Systems
from app.api.v2.future.router import future_router


app.include_router(future_router, prefix="/api/v2")

from app.api.v2 import pwa_notifications, pwa_sync
from app.api.v2.new_routers import sso


app.include_router(pwa_sync.router, prefix="/api/v2")
app.include_router(pwa_notifications.router, prefix="/api/v2")
app.include_router(sso.router, prefix="/api/v2")

# Division modules (Seed Bank, etc.)
# Division modules (Seed Bank, etc.)
# BrAPI v2.1 Phenotyping - Additional endpoints
from app.api.brapi import methods as brapi_methods
from app.api.brapi import observationlevels as brapi_observationlevels
from app.api.brapi import ontologies as brapi_ontologies
from app.api.brapi import scales as brapi_scales
from app.modules.seed_bank.router import router as seed_bank_router

# Space Division Module (Gateway)
from app.modules.space.gateway import router as space_gateway


app.include_router(brapi_methods.router, prefix="/brapi/v2", tags=["Methods"])
app.include_router(brapi_scales.router, prefix="/brapi/v2", tags=["Scales"])
app.include_router(brapi_ontologies.router, prefix="/brapi/v2", tags=["Ontologies"])
app.include_router(brapi_observationlevels.router, prefix="/brapi/v2", tags=["Observation Levels"])

# BrAPI v2.1 Genotyping endpoints
from app.api.brapi import allelematrix as brapi_allelematrix
from app.api.brapi import calls as brapi_calls
from app.api.brapi import callsets as brapi_callsets
from app.api.brapi import maps as brapi_maps
from app.api.brapi import markerpositions as brapi_markerpositions
from app.api.brapi import plates as brapi_plates
from app.api.brapi import references as brapi_references
from app.api.brapi import referencesets as brapi_referencesets
from app.api.brapi import search as brapi_search
from app.api.brapi import variants as brapi_variants
from app.api.brapi import variantsets as brapi_variantsets
from app.api.brapi import vendor as brapi_vendor


app.include_router(brapi_calls.router, prefix="/brapi/v2", tags=["Genotyping - Calls"])
app.include_router(brapi_callsets.router, prefix="/brapi/v2", tags=["Genotyping - CallSets"])
app.include_router(brapi_variants.router, prefix="/brapi/v2", tags=["Genotyping - Variants"])
app.include_router(brapi_variantsets.router, prefix="/brapi/v2", tags=["Genotyping - VariantSets"])
app.include_router(brapi_plates.router, prefix="/brapi/v2", tags=["Genotyping - Plates"])
app.include_router(brapi_references.router, prefix="/brapi/v2", tags=["Genotyping - References"])
app.include_router(brapi_referencesets.router, prefix="/brapi/v2", tags=["Genotyping - ReferenceSets"])
app.include_router(brapi_maps.router, prefix="/brapi/v2", tags=["Genotyping - Maps"])
app.include_router(brapi_markerpositions.router, prefix="/brapi/v2", tags=["Genotyping - Marker Positions"])
app.include_router(brapi_allelematrix.router, prefix="/brapi/v2", tags=["Genotyping - Allele Matrix"])
app.include_router(brapi_search.router, prefix="/brapi/v2", tags=["BrAPI Search"])
app.include_router(brapi_vendor.router, prefix="/brapi/v2", tags=["Genotyping - Vendor"])

# BrAPI Extensions
from app.api.brapi.extensions import iot as brapi_iot


app.include_router(brapi_iot.router, prefix="/brapi/v2", tags=["BrAPI IoT Extension"])

# APEX Features - AI & Analytics
from app.api.v2 import (
    abiotic,
    activity,
    agronomy,
    analytics,
    audit,
    barcode,
    bioinformatics,
    breeding_pipeline,
    breeding_value,
    carbon,
    chaitanya,
    chat,
    climate,
    collaboration_hub,
    compute,
    crop_calendar,
    crop_health,
    crosses,
    crossing_planner,
    data_dictionary,
    data_quality,
    data_sync,
    data_validation,
    data_visualization,
    devguru,
    disease,
    dispatch,
    doubled_haploid,
    dus,
    emissions,
    events,
    export,
    field_environment,
    field_layout,
    field_map,
    field_planning,
    field_scanner,
    forums,
    genetic_diversity,
    genetic_gain,
    genomic_selection,
    genotyping,
    germplasm_collection,
    germplasm_comparison,
    germplasm_search,
    grin,
    gwas,
    gxe,
    haplotype,
    harvest,
    impact,
    insights,
    integrations,
    label_printing,
    languages,
    licensing,
    mas,
    molecular_breeding,
    mta,
    notifications,
    nursery,
    ontology,
    parent_selection,
    parentage,
    passport,
    pedigree,
    performance_ranking,
    phenology,
    phenomic_selection,
    phenotype,
    phenotype_comparison,
    plot_history,
    population_genetics,
    prahari,
    processing,
    profile,
    progeny,
    progress,
    proposals,
    qtl_mapping,
    quality,
    quick_entry,
    rakshaka,
    reports,
    resource_management,
    rls,
    security_audit,
    seed_inventory,
    selection,
    selection_decisions,
    sensors,
    spatial,
    speed_breeding,
    stability_analysis,
    statistics,
    tasks,
    team_management,
    traceability,
    trial_design,
    trial_network,
    trial_planning,
    trial_summary,
    vault_sensors,
    vector,
    vision,
    voice,
    weather,
    workflows,
    yield_gap,
    yield_map,
)


app.include_router(compute.router, prefix="/api/v2", tags=["Compute Engine"])
app.include_router(agronomy.router, prefix="/api/v2", tags=["Agronomy"])
app.include_router(audit.router, prefix="/api/v2", tags=["Audit Trail"])
app.include_router(insights.router, prefix="/api/v2", tags=["AI Insights"])
app.include_router(vector.router, prefix="/api/v2", tags=["Vector Store"])
app.include_router(weather.router, prefix="/api/v2", tags=["Weather Intelligence"])

# Weather Module
from app.modules.weather.router import router as weather_module_router
app.include_router(weather_module_router, prefix="/api/v2", tags=["Weather Service Connection"])

app.include_router(climate.router, prefix="/api/v2", tags=["Climate Analysis"])
app.include_router(carbon.router, prefix="/api/v2", tags=["Carbon Monitoring"])
app.include_router(emissions.router, prefix="/api/v2", tags=["Emissions Tracking"])
app.include_router(impact.router, prefix="/api/v2", tags=["Impact Metrics"])

# Environmental Physics (GDD, Soil Moisture, PTU)
from app.api.v2.environmental import router as environmental_router


app.include_router(environmental_router, prefix="/api/v2/environmental", tags=["Environmental Physics"])

# Agricultural Economics (ROI, Inventory)
from app.api.v2.economics import router as economics_router


app.include_router(economics_router, prefix="/api/v2/economics", tags=["Agricultural Economics"])

# Soil Division
from app.modules.soil.router import router as soil_router
app.include_router(soil_router, prefix="/api/v2/soil", tags=["Soil Division"])

# Biosimulation (Crop Growth Models)
from app.api.v2.biosimulation import router as biosimulation_router


app.include_router(biosimulation_router, prefix="/api/v2/biosimulation", tags=["Biosimulation Engine"])

# Spatial Analysis (GIS & Remote Sensing)
from app.api.v2.spatial import router as spatial_router


app.include_router(spatial_router, prefix="/api/v2/spatial", tags=["Spatial Analysis Engine"])

# Yield Gap Analysis
app.include_router(yield_gap.router, prefix="/api/v2", tags=["Yield Gap Analysis"])

app.include_router(chat.router, prefix="/api/v2", tags=["Veena AI Chat"])
app.include_router(proposals.router, prefix="/api/v2", tags=["Proposals (AI Scribe)"])
app.include_router(crosses.router, prefix="/api/v2", tags=["Cross Prediction"])
app.include_router(integrations.router, prefix="/api/v2", tags=["Integration Hub"])
app.include_router(events.router, prefix="/api/v2", tags=["Event Bus"])
app.include_router(tasks.router, prefix="/api/v2", tags=["Task Queue"])
app.include_router(field_environment.router, prefix="/api/v2", tags=["Field Environment"])
app.include_router(voice.router, prefix="/api/v2", tags=["Veena Voice"])
app.include_router(gxe.router, prefix="/api/v2", tags=["G×E Analysis"])
app.include_router(gwas.router, prefix="/api/v2", tags=["GWAS"])
app.include_router(bioinformatics.router, prefix="/api/v2", tags=["Bioinformatics"])
app.include_router(pedigree.router, prefix="/api/v2", tags=["Pedigree Analysis"])
app.include_router(phenotype.router, prefix="/api/v2", tags=["Phenotype Analysis"])
app.include_router(mas.router, prefix="/api/v2", tags=["Marker-Assisted Selection"])
app.include_router(trial_design.router, prefix="/api/v2", tags=["Trial Design"])
app.include_router(seed_inventory.router, prefix="/api/v2", tags=["Seed Inventory"])
from app.modules.crop_calendar.router import router as crop_calendar_router


app.include_router(crop_calendar_router, prefix="/api/v2")
app.include_router(export.router, prefix="/api/v2", tags=["Data Export"])
app.include_router(quality.router, prefix="/api/v2", tags=["Quality Control"])
app.include_router(passport.router, prefix="/api/v2", tags=["Germplasm Passport"])
app.include_router(ontology.router, prefix="/api/v2", tags=["Trait Ontology"])
app.include_router(nursery.router, prefix="/api/v2", tags=["Nursery Management"])
app.include_router(traceability.router, prefix="/api/v2", tags=["Seed Traceability"])
app.include_router(licensing.router, prefix="/api/v2", tags=["Variety Licensing"])
app.include_router(selection.router, prefix="/api/v2", tags=["Selection Index"])
app.include_router(genetic_gain.router, prefix="/api/v2", tags=["Genetic Gain"])
app.include_router(harvest.router, prefix="/api/v2", tags=["Harvest Management"])
app.include_router(spatial.router, prefix="/api/v2", tags=["Spatial Analysis"])
app.include_router(breeding_value.router, prefix="/api/v2", tags=["Breeding Value"])
app.include_router(disease.router, prefix="/api/v2", tags=["Disease Resistance"])
app.include_router(abiotic.router, prefix="/api/v2", tags=["Abiotic Stress"])
app.include_router(dispatch.router, prefix="/api/v2", tags=["Dispatch Management"])
app.include_router(processing.router, prefix="/api/v2", tags=["Seed Processing"])
app.include_router(sensors.router, prefix="/api/v2", tags=["Sensor Networks"])
app.include_router(forums.router, prefix="/api/v2", tags=["Community Forums"])

# Social Graph
from app.api.v2 import social


app.include_router(social.router, prefix="/api/v2/social")

app.include_router(space_gateway, prefix="/api/v2/space", tags=["Space Division"])
app.include_router(dus.router, prefix="/api/v2", tags=["DUS Testing"])
app.include_router(progress.router, prefix="/api/v2", tags=["Progress Tracker"])
app.include_router(vision.router, prefix="/api/v2", tags=["Vision Training Ground"])
app.include_router(rakshaka.router, prefix="/api/v2", tags=["RAKSHAKA Self-Healing"])
app.include_router(prahari.router, prefix="/api/v2", tags=["PRAHARI Defense"])
app.include_router(chaitanya.router, prefix="/api/v2", tags=["CHAITANYA Orchestrator"])
app.include_router(security_audit.router, prefix="/api/v2", tags=["Security Audit"])
app.include_router(rls.router, prefix="/api/v2", tags=["Row-Level Security"])
app.include_router(grin.router, prefix="/api/v2", tags=["GRIN-Global Integration"])
app.include_router(mta.router, prefix="/api/v2", tags=["Material Transfer Agreements"])
app.include_router(barcode.router, prefix="/api/v2", tags=["Barcode/QR"])
app.include_router(vault_sensors.router, prefix="/api/v2", tags=["Vault Sensors"])
app.include_router(devguru.router, prefix="/api/v2", tags=["DevGuru PhD Mentor"])
app.include_router(selection_decisions.router, prefix="/api/v2", tags=["Selection Decisions"])
app.include_router(parent_selection.router, prefix="/api/v2", tags=["Parent Selection"])
app.include_router(performance_ranking.router, prefix="/api/v2", tags=["Performance Ranking"])
app.include_router(progeny.router, prefix="/api/v2", tags=["Progeny"])
app.include_router(germplasm_comparison.router, prefix="/api/v2", tags=["Germplasm Comparison"])
app.include_router(breeding_pipeline.router, prefix="/api/v2", tags=["Breeding Pipeline"])
app.include_router(genetic_diversity.router, prefix="/api/v2", tags=["Genetic Diversity"])
app.include_router(population_genetics.router, prefix="/api/v2", tags=["Population Genetics"])
app.include_router(qtl_mapping.router, prefix="/api/v2", tags=["QTL Mapping"])
app.include_router(genomic_selection.router, prefix="/api/v2", tags=["Genomic Selection"])
app.include_router(genotyping.router, prefix="/api/v2", tags=["BrAPI Genotyping"])
app.include_router(crossing_planner.router, prefix="/api/v2", tags=["Crossing Planner"])
app.include_router(field_map.router, prefix="/api/v2", tags=["Field Map"])
app.include_router(trial_planning.router, prefix="/api/v2", tags=["Trial Planning"])
app.include_router(data_quality.router, prefix="/api/v2", tags=["Data Quality"])
app.include_router(parentage.router, prefix="/api/v2", tags=["Parentage Analysis"])
app.include_router(haplotype.router, prefix="/api/v2", tags=["Haplotype Analysis"])
app.include_router(trial_network.router, prefix="/api/v2", tags=["Trial Network"])
app.include_router(germplasm_search.router, prefix="/api/v2", tags=["Germplasm Search"])
app.include_router(molecular_breeding.router, prefix="/api/v2", tags=["Molecular Breeding"])
app.include_router(phenomic_selection.router, prefix="/api/v2", tags=["Phenomic Selection"])
app.include_router(speed_breeding.router, prefix="/api/v2", tags=["Speed Breeding"])
app.include_router(doubled_haploid.router, prefix="/api/v2", tags=["Doubled Haploid"])
app.include_router(field_planning.router, prefix="/api/v2", tags=["Field Planning"])
app.include_router(resource_management.router, prefix="/api/v2", tags=["Resource Management"])
app.include_router(field_scanner.router, prefix="/api/v2", tags=["Field Scanner"])
app.include_router(label_printing.router, prefix="/api/v2", tags=["Label Printing"])
app.include_router(quick_entry.router, prefix="/api/v2", tags=["Quick Entry"])
app.include_router(phenology.router, prefix="/api/v2", tags=["Phenology Tracker"])
app.include_router(plot_history.router, prefix="/api/v2", tags=["Plot History"])
app.include_router(statistics.router, prefix="/api/v2", tags=["Statistics"])
app.include_router(crop_health.router, prefix="/api/v2", tags=["Crop Health"])
app.include_router(notifications.router, prefix="/api/v2", tags=["Notifications"])
app.include_router(activity.router, prefix="/api/v2", tags=["Activity"])
app.include_router(data_validation.router, prefix="/api/v2", tags=["Data Validation"])
app.include_router(profile.router, prefix="/api/v2", tags=["Profile"])
app.include_router(team_management.router, prefix="/api/v2", tags=["Team Management"])
app.include_router(data_dictionary.router, prefix="/api/v2", tags=["Data Dictionary"])
app.include_router(germplasm_collection.router, prefix="/api/v2", tags=["Germplasm Collections"])

# Data Import
from app.api.v2.import_api import router as import_router


app.include_router(import_router, prefix="/api/v2", tags=["Data Import"])

# Collaboration & Team
from app.api.v2 import collaboration


app.include_router(collaboration.router, prefix="/api/v2", tags=["Collaboration"])

# Offline Sync
from app.api.v2 import offline_sync


app.include_router(offline_sync.router, prefix="/api/v2", tags=["Offline Sync"])

# System Settings
from app.api.v2 import system_settings


app.include_router(system_settings.router, prefix="/api/v2", tags=["System Settings"])

# External Services Status
from app.api.v2 import external_services


app.include_router(external_services.router, prefix="/api/v2", tags=["External Services"])

# Backup & Restore
from app.api.v2 import backup


app.include_router(backup.router, prefix="/api/v2", tags=["Backup"])


# Workflow Automation
app.include_router(workflows.router, prefix="/api/v2", tags=["Workflow Automation"])

# Language Settings
app.include_router(languages.router, prefix="/api/v2", tags=["Language Settings"])

# Analytics
app.include_router(analytics.router, prefix="/api/v2", tags=["Apex Analytics"])

# Advanced Reports
app.include_router(reports.router, prefix="/api/v2", tags=["Advanced Reports"])

# Compliance
from app.api.v2 import compliance


app.include_router(compliance.router, prefix="/api/v2", tags=["Compliance"])

# Data Sync
app.include_router(data_sync.router, prefix="/api/v2", tags=["Data Sync"])

# Collaboration Hub
app.include_router(collaboration_hub.router, prefix="/api/v2", tags=["Collaboration Hub"])

# Field Layout
app.include_router(field_layout.router, prefix="/api/v2", tags=["Field Layout"])

# Trial Summary
app.include_router(trial_summary.router, prefix="/api/v2", tags=["Trial Summary"])

# Data Visualization
app.include_router(data_visualization.router, prefix="/api/v2", tags=["Data Visualization"])

# Future Endpoints - Crop Intelligence
from app.api.v2.future import (
    carbon_sequestration,
    crop_suitability,
    disease_risk_forecast,
    fertilizer_recommendation,
    gdd,
    ipm_strategy,
    irrigation_schedule,
    pest_observation,
    soil_health,
    soil_moisture,
    soil_test,
    spray_application,
    water_balance,
    yield_prediction,
)


app.include_router(crop_suitability.router, prefix="/api/v2/future", tags=["Crop Suitability"])
app.include_router(gdd.router, prefix="/api/v2/future", tags=["Growing Degree Days"])
app.include_router(soil_test.router, prefix="/api/v2/future", tags=["Soil Tests"])
app.include_router(fertilizer_recommendation.router, prefix="/api/v2/future", tags=["Fertilizer Recommendations"])
app.include_router(soil_health.router, prefix="/api/v2/future", tags=["Soil Health"])
app.include_router(carbon_sequestration.router, prefix="/api/v2/future", tags=["Carbon Sequestration"])
app.include_router(pest_observation.router, prefix="/api/v2/future", tags=["Pest Observations"])
app.include_router(disease_risk_forecast.router, prefix="/api/v2/future", tags=["Disease Risk Forecasts"])
app.include_router(spray_application.router, prefix="/api/v2/future", tags=["Spray Applications"])
app.include_router(ipm_strategy.router, prefix="/api/v2/future", tags=["IPM Strategies"])
app.include_router(irrigation_schedule.router, prefix="/api/v2/future", tags=["Irrigation Schedules"])
app.include_router(water_balance.router, prefix="/api/v2/future", tags=["Water Balance"])
app.include_router(soil_moisture.router, prefix="/api/v2/future", tags=["Soil Moisture"])

# IoT Extension
from app.api.v2.iot import devices as iot_devices
from app.api.v2.iot import telemetry as iot_telemetry
app.include_router(iot_devices.router, prefix="/api/v2")
app.include_router(iot_telemetry.router, prefix="/api/v2")

# Yield Map
app.include_router(yield_map.router, prefix="/api/v2", tags=["Yield Map"])

# Phenotype Comparison
app.include_router(phenotype_comparison.router, prefix="/api/v2", tags=["Phenotype Comparison"])

# Yield Prediction
app.include_router(yield_prediction.router, prefix="/api/v2/future", tags=["Yield Prediction"])

# Stability Analysis
app.include_router(stability_analysis.router, prefix="/api/v2", tags=["Stability Analysis"])

# Field Book
from app.api.v2 import field_book


app.include_router(field_book.router, prefix="/api/v2", tags=["Field Book"])

# Nursery Management (Seedling Production)
from app.api.v2 import nursery_management


app.include_router(nursery_management.router, prefix="/api/v2", tags=["Nursery Management"])

# Warehouse Management
from app.api.v2 import warehouse


app.include_router(warehouse.router, prefix="/api/v2", tags=["Warehouse Management"])

# Metrics - Single Source of Truth
from app.api.v2 import metrics


app.include_router(metrics.router, prefix="/api/v2", tags=["Metrics"])

# RBAC (Role-Based Access Control)
from app.api.v2 import rbac


app.include_router(rbac.router, prefix="/api/v2", tags=["RBAC"])

# Dock Preferences (Mahasarthi Navigation)
from app.api.v2 import dock


app.include_router(dock.router, prefix="/api/v2", tags=["Dock"])


# Division modules
app.include_router(seed_bank_router, prefix="/api/v2", tags=["Seed Bank"])

# Robotics Simulator
try:
    from app.api.v2 import robotics

    app.include_router(robotics.router, prefix="/api/v2/robotics", tags=["Robotics Simulator"])
except Exception as robotics_import_error:
    logger.warning("Robotics routes disabled due to missing dependencies: %s", robotics_import_error)

# Performance Optimization
from app.api.v2 import performance
app.include_router(performance.router, prefix="/api/v2", tags=["Performance Optimization"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
