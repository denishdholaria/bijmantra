import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_plates_unauthenticated(async_db_session: AsyncSession):
    """
    Test that GET /brapi/v2/plates returns 401 for unauthenticated users.
    """
    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/brapi/v2/plates")
        assert response.status_code == 401

        # Test other endpoints too
        response = await client.get("/brapi/v2/plates/plate1")
        assert response.status_code == 401

        # Test CREATE (POST)
        # Note: This endpoint was already secured via `get_organization_id` dependency,
        # which implicitly requires `get_current_active_user`.
        # This test ensures it remains secure if that dependency is refactored.
        response = await client.post("/brapi/v2/plates", json=[])
        assert response.status_code == 401

        response = await client.put("/brapi/v2/plates", json=[])
        assert response.status_code == 401

        response = await client.delete("/brapi/v2/plates/plate1")
        assert response.status_code == 401

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_plates_authenticated(authenticated_client: AsyncClient):
    """
    Test that GET /brapi/v2/plates returns 200 for authenticated users.
    """
    response = await authenticated_client.get("/brapi/v2/plates")
    assert response.status_code == 200
    # Response structure check
    data = response.json()
    assert "result" in data
    assert "data" in data["result"]
