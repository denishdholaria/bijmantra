"""
Middleware configuration for Bijmantra API.

This module centralizes all middleware setup following the hot-file extraction protocol.
Extracted from main.py as part of Task 16.
"""

import logging
import os
import secrets
from collections.abc import Awaitable, Callable
from hashlib import sha256

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.config import settings
from app.middleware.request_tracing import TRACE_ID_HEADER, configure_trace_logging

logger = logging.getLogger(__name__)

# Static BrAPI cache paths
STATIC_BRAPI_CACHE_PATHS = {"/brapi/v2/serverinfo"}


def configure_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(trace_id)s | %(message)s",
    )
    configure_trace_logging()


def initialize_sentry():
    """Initialize Sentry for error tracking."""
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.getenv('ENVIRONMENT', 'development'),
        )
        logger.info("Sentry initialized")


def add_cors_middleware(app: FastAPI):
    """Add CORS middleware with restricted methods (M1 security fix)."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            TRACE_ID_HEADER,
            "X-Requested-With",
            "Accept",
            "Origin",
            "baggage",
            "sentry-trace",
            "traceparent",
        ],
        expose_headers=[TRACE_ID_HEADER],
    )
    logger.info("CORS middleware enabled")


async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Function middleware for security headers (avoids BaseHTTPMiddleware overhead)."""
    # Generate nonce for CSP
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Dynamic CSP Policy based on path
    path = request.url.path
    if path.startswith(("/docs", "/redoc")):
        # Relaxed policy for documentation
        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            f"img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            f"font-src 'self' data: https://cdn.jsdelivr.net; "
            f"connect-src 'self';"
        )
    else:
        # Strict policy for API endpoints
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


async def brapi_static_cache_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Adds lightweight ETag + Cache-Control handling for static BrAPI responses."""
    response = await call_next(request)

    if (request.method != "GET" or
        request.url.path not in STATIC_BRAPI_CACHE_PATHS or
        response.status_code != 200):
        return response

    # Skip if upstream already set validators
    if "etag" in response.headers:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    etag = f'W/"{sha256(body).hexdigest()}"'
    if request.headers.get("if-none-match") == etag:
        return StarletteResponse(
            status_code=304,
            headers={"ETag": etag, "Cache-Control": "public, max-age=300"}
        )

    headers = dict(response.headers)
    headers["ETag"] = etag
    headers["Cache-Control"] = "public, max-age=300"

    return StarletteResponse(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type
    )


def add_audit_middleware(app: FastAPI):
    """Add audit middleware (non-blocking inserts + emergency lockdown gate)."""
    try:
        from app.middleware.audit_middleware import AuditMiddleware
        app.add_middleware(AuditMiddleware)
        logger.info("Audit middleware enabled")
    except Exception as e:
        logger.warning("Audit middleware not available: %s", e)


def add_route_profiler_middleware(app: FastAPI):
    """Add route profiler middleware (development only)."""
    if os.getenv("ENVIRONMENT", "development") == "development":
        try:
            from app.middleware.route_profiler import RouteProfilerMiddleware
            app.add_middleware(RouteProfilerMiddleware)
            logger.info("Route profiler middleware enabled")
        except Exception as e:
            logger.warning("Route profiler unavailable: %s", e)


def add_security_middleware(app: FastAPI):
    """Add security middleware (PRAHARI integration)."""
    try:
        from app.middleware.security import SecurityMiddleware
        app.add_middleware(SecurityMiddleware, enabled=True)
        logger.info("Security middleware enabled")
    except Exception as e:
        logger.warning("Security middleware not available: %s", e)


def add_tenant_context_middleware(app: FastAPI):
    """Add tenant context middleware (RLS support)."""
    try:
        from app.middleware.tenant_context import TenantContextMiddleware
        app.add_middleware(TenantContextMiddleware)
        logger.info("Tenant context middleware enabled")
    except Exception as e:
        logger.warning("Tenant context middleware not available: %s", e)


def add_request_tracing_middleware(app: FastAPI):
    """Add request tracing middleware."""
    try:
        from app.middleware.request_tracing import RequestTracingMiddleware
        app.add_middleware(RequestTracingMiddleware)
        logger.info("Request tracing middleware enabled")
    except Exception as e:
        logger.warning("Request tracing middleware not available: %s", e)


def configure_all_middleware(app: FastAPI):
    """
    Configure all middleware for the FastAPI application.
    
    This is the main entry point for middleware setup.
    Order matters: middleware is applied in reverse order of addition.
    """
    # Initialize logging and Sentry first
    configure_logging()
    initialize_sentry()
    
    # Add middleware in reverse order of execution
    add_cors_middleware(app)
    
    # Function middleware (executed in order of addition)
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(brapi_static_cache_middleware)
    
    logger.info("Security headers middleware enabled")
    
    # Class-based middleware (executed in reverse order)
    add_audit_middleware(app)
    add_route_profiler_middleware(app)
    add_security_middleware(app)
    add_tenant_context_middleware(app)
    add_request_tracing_middleware(app)
