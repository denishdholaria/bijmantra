"""
Bijmantra - BrAPI v2.1 Plant Breeding Application
FastAPI Backend with Real-time Collaboration
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from app.core.config import settings

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
    print("[Bijmantra] Starting up...")
    
    # Initialize Meilisearch
    try:
        from app.core.meilisearch import meilisearch_service
        if meilisearch_service.connect():
            meilisearch_service.setup_indexes()
    except Exception as e:
        print(f"[Meilisearch] Initialization skipped: {e}")
    
    # Start background task queue
    try:
        from app.services.task_queue import task_queue
        await task_queue.start()
    except Exception as e:
        print(f"[TaskQueue] Initialization skipped: {e}")
    
    # Initialize Redis security storage
    try:
        from app.services.redis_security import init_redis_security
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            await init_redis_security(redis_url)
            print("[Redis] Security storage initialized")
        else:
            print("[Redis] No REDIS_URL configured, using in-memory storage")
    except Exception as e:
        print(f"[Redis] Security storage initialization skipped: {e}")
    
    yield
    
    # Shutdown
    print("[Bijmantra] Shutting down...")
    
    # Stop task queue
    try:
        from app.services.task_queue import task_queue
        await task_queue.stop()
    except Exception:
        pass

# Create FastAPI app
app = FastAPI(
    title="Bijmantra API",
    description="BrAPI v2.1 compliant Plant Breeding Application with Real-time Collaboration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware (OWASP recommendations)
try:
    from app.middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(
        SecurityHeadersMiddleware, 
        enabled=True,
        csp_policy="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:;"
    )
    print("[Security] Security headers middleware enabled")
except Exception as e:
    print(f"[Security] Security headers middleware not available: {e}")

# Security middleware (PRAHARI integration)
try:
    from app.middleware.security import SecurityMiddleware
    app.add_middleware(SecurityMiddleware, enabled=True)
    print("[PRAHARI] Security middleware enabled")
except Exception as e:
    print(f"[PRAHARI] Security middleware not available: {e}")

# Tenant context middleware (RLS support)
try:
    from app.middleware.tenant_context import TenantContextMiddleware
    app.add_middleware(TenantContextMiddleware)
    print("[RLS] Tenant context middleware enabled")
except Exception as e:
    print(f"[RLS] Tenant context middleware not available: {e}")

# Mount Socket.IO
try:
    from app.core.socketio import socket_app
    app.mount("/ws", socket_app)
    print("[Socket.IO] Mounted at /ws")
except Exception as e:
    print(f"[Socket.IO] Not available: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Bijmantra API",
        "version": "0.1.0",
        "brapi_version": "2.1",
        "docs": "/docs",
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# API Statistics
@app.get("/api/stats")
async def api_stats():
    """API statistics and version info"""
    return {
        "name": "Bijmantra API",
        "version": "0.1.0",
        "brapi_version": "2.1",
        "total_endpoints": 572,
        "modules": [
            "Authentication", "BrAPI Core", "Compute Engine", "AI Insights",
            "Vector Store", "Weather", "Veena AI", "Cross Prediction",
            "Integration Hub", "Event Bus", "Task Queue", "Field Environment",
            "Voice", "G×E Analysis", "GWAS", "Bioinformatics", "Pedigree",
            "Phenotype", "MAS", "Trial Design", "Seed Inventory", "Crop Calendar",
            "Data Export", "Quality Control", "Germplasm Passport", "Trait Ontology",
            "Nursery Management", "Seed Traceability", "Variety Licensing",
            "Selection Index", "Genetic Gain", "Harvest Management",
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
            "contactEmail": "admin@bijmantra.org",
            "documentationURL": "https://github.com/yourusername/bijmantra",
            "location": "India",
            "organizationName": "Bijmantra",
            "organizationURL": "https://bijmantra.org",
            "serverDescription": "Bijmantra - Plant Breeding Application",
            "serverName": "Bijmantra",
        },
    }

# Import routers
from app.api import auth
from app.api.v2.core import programs, locations, trials, studies, seasons
from app.api.v2 import search, compute, audit, insights, vector, weather, chat, crosses, integrations, events, tasks, field_environment, voice, gxe, gwas, bioinformatics, pedigree, phenotype, mas, trial_design, seed_inventory, crop_calendar, export, quality, passport, ontology, nursery, traceability, licensing, selection, genetic_gain, harvest, spatial, breeding_value, disease, abiotic
from app.api.v2 import dispatch, processing, sensors, forums, solar, space, dus, progress, rakshaka, vision, prahari, chaitanya, security_audit, rls, grin, mta, barcode, vault_sensors, devguru, selection_decisions, parent_selection, performance_ranking, progeny, germplasm_comparison, breeding_pipeline

# Division modules
from app.modules.seed_bank import router as seed_bank_router

# Auth routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Search routes
app.include_router(search.router, prefix="/brapi/v2", tags=["Search"])

# BrAPI v2.1 Core routes
app.include_router(programs.router, prefix="/brapi/v2", tags=["Core - Programs"])
app.include_router(locations.router, prefix="/brapi/v2", tags=["Core - Locations"])
app.include_router(trials.router, prefix="/brapi/v2", tags=["Core - Trials"])
app.include_router(studies.router, prefix="/brapi/v2", tags=["Core - Studies"])
app.include_router(seasons.router, prefix="/brapi/v2", tags=["Core - Seasons"])

# BrAPI v2.1 Germplasm routes
from app.api.brapi import germplasm as brapi_germplasm
from app.api.brapi import crosses as brapi_crosses
from app.api.brapi import traits as brapi_traits
from app.api.brapi import variables as brapi_variables
from app.api.brapi import observations as brapi_observations
from app.api.brapi import observationunits as brapi_observationunits
from app.api.brapi import events as brapi_events
from app.api.brapi import images as brapi_images
from app.api.brapi import samples as brapi_samples
from app.api.brapi import seedlots as brapi_seedlots
from app.api.brapi import people as brapi_people

app.include_router(brapi_germplasm.router, prefix="/brapi/v2", tags=["Germplasm"])
app.include_router(brapi_crosses.router, prefix="/brapi/v2", tags=["Crosses"])
app.include_router(brapi_traits.router, prefix="/brapi/v2", tags=["Traits"])
app.include_router(brapi_variables.router, prefix="/brapi/v2", tags=["Observation Variables"])
app.include_router(brapi_observations.router, prefix="/brapi/v2", tags=["Observations"])
app.include_router(brapi_observationunits.router, prefix="/brapi/v2", tags=["Observation Units"])
app.include_router(brapi_events.router, prefix="/brapi/v2", tags=["Events"])
app.include_router(brapi_images.router, prefix="/brapi/v2", tags=["Images"])
app.include_router(brapi_samples.router, prefix="/brapi/v2", tags=["Samples"])
app.include_router(brapi_seedlots.router, prefix="/brapi/v2", tags=["Seed Lots"])
app.include_router(brapi_people.router, prefix="/brapi/v2", tags=["People"])

# APEX Features - AI & Analytics
app.include_router(compute.router, prefix="/api/v2", tags=["Compute Engine"])
app.include_router(audit.router, prefix="/api/v2", tags=["Audit Trail"])
app.include_router(insights.router, prefix="/api/v2", tags=["AI Insights"])
app.include_router(vector.router, prefix="/api/v2", tags=["Vector Store"])
app.include_router(weather.router, prefix="/api/v2", tags=["Weather Intelligence"])
app.include_router(chat.router, prefix="/api/v2", tags=["Veena AI Chat"])
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
app.include_router(crop_calendar.router, prefix="/api/v2", tags=["Crop Calendar"])
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
app.include_router(solar.router, prefix="/api/v2", tags=["Sun-Earth Systems"])
app.include_router(space.router, prefix="/api/v2", tags=["Space Research"])
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

# Division modules
app.include_router(seed_bank_router, prefix="/api/v2", tags=["Seed Bank"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
