"""
Bijmantra - BrAPI v2.1 Plant Breeding Application
FastAPI Backend with Real-time Collaboration

This is the thin app factory following the hot-file extraction protocol.
Extracted startup logic into focused modules as part of Task 16.

See:
- app/startup/middleware.py - Middleware configuration
- app/startup/database.py - Database and service initialization
- app/startup/config.py - Application factory
- app/startup/routes.py - Route registration
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Request
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.core.config import settings
from app.startup.config import create_app, mount_socketio
from app.startup.middleware import configure_all_middleware
from app.startup.routes import register_all_routes

logger = logging.getLogger(__name__)

# Create FastAPI app
app = create_app()

# Configure middleware
configure_all_middleware(app)

# Mount Socket.IO
mount_socketio(app)

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


# =============================================================================
# CORE ENDPOINTS
# =============================================================================


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Bijmantra API",
        "version": settings.APP_VERSION,
        "brapi_version": settings.BRAPI_VERSION,
        "docs": "/docs",
    }


async def _probe_postgres_health() -> dict:
    """Probe PostgreSQL health."""
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "critical": True}
    except Exception as exc:
        return {
            "status": "critical",
            "critical": True,
            "error": str(exc)[:120],
        }


async def _probe_redis_health() -> dict:
    """Probe Redis health."""
    try:
        from app.core.redis import redis_client

        if redis_client.is_available and redis_client._client:
            await redis_client._client.ping()
            return {"status": "healthy", "critical": False}

        return {"status": "degraded", "critical": False, "detail": "in-memory fallback"}
    except Exception as exc:
        return {
            "status": "degraded",
            "critical": False,
            "error": str(exc)[:120],
        }


async def _probe_meilisearch_health() -> dict:
    """Probe Meilisearch health."""
    try:
        from app.core.meilisearch import meilisearch_service

        if meilisearch_service.connected and meilisearch_service.client:
            meilisearch_service.client.health()
            return {"status": "healthy", "critical": False}

        return {"status": "degraded", "critical": False, "detail": "not connected"}
    except Exception as exc:
        return {
            "status": "degraded",
            "critical": False,
            "error": str(exc)[:120],
        }


async def _probe_task_queue_health() -> dict:
    """Probe task queue health."""
    try:
        from app.services.task_queue import task_queue

        if task_queue.is_running:
            stats = task_queue.get_stats()
            return {
                "status": "healthy",
                "critical": False,
                "stats": {
                    "queue_size": stats["queue_size"],
                    "running": stats["running"],
                    "pending": stats["pending"],
                    "max_concurrent": stats["max_concurrent"],
                },
            }

        return {"status": "degraded", "critical": False, "detail": "task queue not running"}
    except Exception as exc:
        return {
            "status": "degraded",
            "critical": False,
            "error": str(exc)[:120],
        }


@app.get("/health")
async def health_check():
    """
    Dependency-aware health endpoint (ADR-003).

    Probes core runtime dependencies and reports overall status:
      - healthy:  all dependencies reachable
      - degraded: non-critical dependency unreachable (Redis, Meilisearch)
      - critical: critical dependency unreachable (PostgreSQL)
    """
    dependencies: dict[str, dict] = {}

    dependencies["postgres"] = await _probe_postgres_health()
    dependencies["redis"] = await _probe_redis_health()
    dependencies["meilisearch"] = await _probe_meilisearch_health()
    dependencies["task_queue"] = await _probe_task_queue_health()

    # Overall status
    statuses = [d["status"] for d in dependencies.values()]
    if "critical" in statuses:
        overall = "critical"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "dependencies": dependencies,
    }


def _load_metrics_sync(path: Path) -> dict[str, int]:
    """Helper to load API metrics synchronously for offloading to a thread."""
    with open(path) as f:
        metrics = json.load(f)

    api_metrics = metrics.get("api", {})
    brapi_published_endpoints = api_metrics.get(
        "brapiPublishedEndpoints",
        201,
    )
    brapi_exposed_endpoints = api_metrics.get(
        "brapiExposedEndpoints",
        api_metrics.get("brapiEndpoints", brapi_published_endpoints),
    )
    return {
        "totalEndpoints": api_metrics.get("totalEndpoints", 1728),
        "brapiEndpoints": brapi_exposed_endpoints,
        "brapiPublishedEndpoints": brapi_published_endpoints,
        "brapiExposedEndpoints": brapi_exposed_endpoints,
        "brapiCoverage": api_metrics.get("brapiCoverage", 100),
    }


@app.get("/api/stats")
async def api_stats():
    """API statistics and version info - reads from metrics.json with failsafe"""
    repo_root = Path(__file__).resolve().parents[2]
    metrics_paths = [
        repo_root / "metrics.json",
    ]

    api_metrics = {
        "totalEndpoints": 1728,
        "brapiEndpoints": 201,
        "brapiPublishedEndpoints": 201,
        "brapiExposedEndpoints": 201,
        "brapiCoverage": 100,
    }

    for metrics_path in metrics_paths:
        if metrics_path.exists():
            try:
                # Offload blocking I/O and JSON parsing to a thread
                api_metrics = await asyncio.to_thread(_load_metrics_sync, metrics_path)
                break
            except (OSError, json.JSONDecodeError):
                continue

    return {
        "name": "Bijmantra API",
        "version": settings.APP_VERSION,
        "brapi_version": settings.BRAPI_VERSION,
        "total_endpoints": api_metrics["totalEndpoints"],
        "brapi_endpoints": api_metrics["brapiEndpoints"],
        "brapi_published_endpoints": api_metrics["brapiPublishedEndpoints"],
        "brapi_exposed_endpoints": api_metrics["brapiExposedEndpoints"],
        "brapi_coverage": api_metrics["brapiCoverage"],
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
            "location": "Global",
            "organizationName": "Bijmantra",
            "organizationURL": "https://gitlab.com/denishdholaria/bijmantraorg",
            "serverDescription": "Bijmantra - Plant Breeding Application",
            "serverName": "Bijmantra",
        },
    }


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

register_all_routes(app)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
