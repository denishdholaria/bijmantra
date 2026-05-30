"""
Unit tests for Core Domain Router
Tests the core domain API endpoints at /api/v2/core
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


def _route_paths() -> set[str]:
    return {getattr(route, "path", "") for route in app.routes}


def test_apex_module_routes_use_canonical_prefixes():
    """Module routers should be mounted below the startup /api/v2 prefix only once."""
    route_paths = _route_paths()

    assert not any("/api/v2/api/v2" in path for path in route_paths)
    assert not any("/core/core" in path for path in route_paths)
    assert "/api/v2/core/health" in route_paths
    assert "/api/v2/seed-bank/vaults" in route_paths
    assert "/api/v2/crop-calendar/activity-types" in route_paths


def test_incomplete_soil_module_is_not_exposed_on_canonical_api():
    route_paths = _route_paths()

    assert "/api/v2/soil/nutrient-tests" not in route_paths


@pytest.mark.asyncio
async def test_health_check():
    """Test the core domain health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v2/core/health")
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["domain"] == "core"
    assert "services" in data
    assert "authorization" in data["services"]
    assert "audit" in data["services"]


@pytest.mark.asyncio
async def test_rate_limit_status():
    """Test the rate limit status endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v2/core/rate-limits/status?limit_type=api")
        
    assert response.status_code == 200
    data = response.json()
    assert "allowed" in data
    assert "remaining" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_check_permission_requires_auth():
    """Test that permission check endpoint requires authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v2/core/permissions/check",
            json={"permission_code": "test.permission"}
        )
        
    # Should return 401 or 403 without authentication
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_current_user_requires_auth():
    """Test that get current user endpoint requires authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v2/core/users/me")
        
    # Should return 401 or 403 without authentication
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_my_permissions_requires_auth():
    """Test that get my permissions endpoint requires authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v2/core/permissions/me")
        
    # Should return 401 or 403 without authentication
    assert response.status_code in [401, 403]
