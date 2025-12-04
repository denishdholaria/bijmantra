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
    
    yield
    
    # Shutdown
    print("[Bijmantra] Shutting down...")

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
from app.api.v2.core import programs, locations, trials, studies
from app.api.v2 import search, compute, audit, insights, vector, weather

# Auth routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Search routes
app.include_router(search.router, prefix="/brapi/v2", tags=["Search"])

# BrAPI v2.1 Core routes
app.include_router(programs.router, prefix="/brapi/v2", tags=["Core - Programs"])
app.include_router(locations.router, prefix="/brapi/v2", tags=["Core - Locations"])
app.include_router(trials.router, prefix="/brapi/v2", tags=["Core - Trials"])
app.include_router(studies.router, prefix="/brapi/v2", tags=["Core - Studies"])

# APEX Features - AI & Analytics
app.include_router(compute.router, prefix="/api/v2", tags=["Compute Engine"])
app.include_router(audit.router, prefix="/api/v2", tags=["Audit Trail"])
app.include_router(insights.router, prefix="/api/v2", tags=["AI Insights"])
app.include_router(vector.router, prefix="/api/v2", tags=["Vector Store"])
app.include_router(weather.router, prefix="/api/v2", tags=["Weather Intelligence"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
