"""
Bijmantra - BrAPI v2.1 Plant Breeding Application
FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Bijmantra API",
    description="BrAPI v2.1 compliant Plant Breeding Application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Auth routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# BrAPI v2.1 Core routes
app.include_router(programs.router, prefix="/brapi/v2", tags=["Core - Programs"])
app.include_router(locations.router, prefix="/brapi/v2", tags=["Core - Locations"])
app.include_router(trials.router, prefix="/brapi/v2", tags=["Core - Trials"])
app.include_router(studies.router, prefix="/brapi/v2", tags=["Core - Studies"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
