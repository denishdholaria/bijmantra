import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Bijmantra API"
    assert "version" in data
    assert "brapi_version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "critical"]
    assert "dependencies" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_brapi_serverinfo():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/brapi/v2/serverinfo")
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "serverName" in data["result"]
