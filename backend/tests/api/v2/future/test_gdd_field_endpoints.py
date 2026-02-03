# backend/tests/api/v2/future/test_gdd_field_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_get_field_gdd_summary(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v2/gdd/field/1/summary")
    assert response.status_code == 200
    # In a real test, we'd check the response body more thoroughly.
    assert "field_id" in response.json()
