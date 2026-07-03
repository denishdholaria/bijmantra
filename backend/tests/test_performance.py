"""
Tests for Performance Optimization API
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.performance

@pytest.mark.asyncio
async def test_database_index_crud(superuser_client: AsyncClient):
    """Test CRUD for DatabaseIndex"""

    # Create
    response = await superuser_client.post(
        "/api/v2/database-indexes",
        json={
            "table_name": "users",
            "index_name": "ix_users_email",
            "columns": ["email"],
            "is_unique": True,
            "description": "Unique email index"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "users"
    assert data["index_name"] == "ix_users_email"
    index_id = data["id"]

    # List
    response = await superuser_client.get("/api/v2/database-indexes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Get
    response = await superuser_client.get(f"/api/v2/database-indexes/{index_id}")
    assert response.status_code == 200
    assert response.json()["id"] == index_id

    # Update
    response = await superuser_client.put(
        f"/api/v2/database-indexes/{index_id}",
        json={"description": "Updated description"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"

    # Delete
    response = await superuser_client.delete(f"/api/v2/database-indexes/{index_id}")
    assert response.status_code == 200
    assert response.json() is True

    # Verify Delete
    response = await superuser_client.get(f"/api/v2/database-indexes/{index_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_cache_crud(superuser_client: AsyncClient):
    """Test CRUD for QueryCache"""

    # Create
    response = await superuser_client.post(
        "/api/v2/query-caches",
        json={
            "query_hash": "abc123hash",
            "query_text": "SELECT * FROM users",
            "hit_count": 10,
            "miss_count": 2,
            "is_active": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_hash"] == "abc123hash"
    cache_id = data["id"]

    # Get
    response = await superuser_client.get(f"/api/v2/query-caches/{cache_id}")
    assert response.status_code == 200

    # Update
    response = await superuser_client.put(
        f"/api/v2/query-caches/{cache_id}",
        json={"hit_count": 11}
    )
    assert response.status_code == 200
    assert response.json()["hit_count"] == 11


@pytest.mark.asyncio
async def test_frontend_bundle_crud(superuser_client: AsyncClient):
    """Test CRUD for FrontendBundle"""

    # Create
    response = await superuser_client.post(
        "/api/v2/frontend-bundles",
        json={
            "name": "main.js",
            "size_kb": 1024.5,
            "load_time_ms": 150,
            "build_id": "build-001",
            "status": "active"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "main.js"

@pytest.mark.asyncio
async def test_asset_optimization_crud(superuser_client: AsyncClient):
    """Test CRUD for AssetOptimization"""

    # Create
    response = await superuser_client.post(
        "/api/v2/asset-optimizations",
        json={
            "asset_path": "/images/logo.png",
            "original_size_kb": 500.0,
            "optimized_size_kb": 250.0,
            "compression_ratio": 0.5,
            "optimization_method": "webp"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["asset_path"] == "/images/logo.png"

@pytest.mark.asyncio
async def test_server_response_crud(superuser_client: AsyncClient):
    """Test CRUD for ServerResponse"""

    # Create
    response = await superuser_client.post(
        "/api/v2/server-responses",
        json={
            "endpoint": "/api/v1/users",
            "method": "GET",
            "status_code": 200,
            "response_time_ms": 45.6,
            "client_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["endpoint"] == "/api/v1/users"
