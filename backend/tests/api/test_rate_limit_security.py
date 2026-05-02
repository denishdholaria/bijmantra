import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.main import app

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_rate_limit_reset_security(client: AsyncClient):
    """
    Test that rate limit reset endpoints are secured by DEBUG mode
    AND the X-RateLimit-Reset-Token header.
    """
    # 1. Valid token + DEBUG=True (Default in test env)
    # The default token is 'dev-reset-token' as set in config.py for DEBUG=True

    # Verify current settings
    assert settings.DEBUG is True
    # If this fails, it means the test env isn't setting up defaults as expected
    if not settings.RATE_LIMIT_RESET_TOKEN:
        settings.RATE_LIMIT_RESET_TOKEN = "dev-reset-token"

    assert settings.RATE_LIMIT_RESET_TOKEN == "dev-reset-token"

    # Case 1: Success
    response = await client.post(
        "/api/auth/reset-rate-limit",
        headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"

    # Case 2: Invalid token
    response = await client.post(
        "/api/auth/reset-rate-limit",
        headers={"X-RateLimit-Reset-Token": "wrong-token"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid or missing rate limit reset token" in response.json()["detail"]

    # Case 3: Missing token
    response = await client.post("/api/auth/reset-rate-limit")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Invalid or missing rate limit reset token" in response.json()["detail"]

    # Case 4: DEBUG=False (Simulated)
    # We need to temporarily patch settings.DEBUG using object.__setattr__
    original_debug = settings.DEBUG
    object.__setattr__(settings, 'DEBUG', False)
    try:
        # Even with valid token, it should fail
        response = await client.post(
            "/api/auth/reset-rate-limit",
            headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Rate limit reset is only available in development mode" in response.json()["detail"]
    finally:
        object.__setattr__(settings, 'DEBUG', original_debug)

@pytest.mark.asyncio
async def test_reset_all_rate_limits_security(client: AsyncClient):
    """Test security for reset-all endpoint"""
    # If this fails, it means the test env isn't setting up defaults as expected
    if not settings.RATE_LIMIT_RESET_TOKEN:
        settings.RATE_LIMIT_RESET_TOKEN = "dev-reset-token"

    # Success
    response = await client.post(
        "/api/auth/reset-all-rate-limits",
        headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Fail
    response = await client.post(
        "/api/auth/reset-all-rate-limits",
        headers={"X-RateLimit-Reset-Token": "wrong"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
