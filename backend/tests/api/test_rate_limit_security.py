import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.api import auth as auth_api
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
    original_debug = settings.DEBUG
    original_token = settings.RATE_LIMIT_RESET_TOKEN
    object.__setattr__(settings, "DEBUG", True)
    object.__setattr__(settings, "RATE_LIMIT_RESET_TOKEN", "dev-reset-token")
    try:
        # Case 1: Success
        auth_api._FAILED_LOGIN_ATTEMPTS["admin@bijmantra.org"] = {"count": 5, "locked_until": None}
        response = await client.post(
            "/api/auth/reset-rate-limit",
            headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"
        assert auth_api._FAILED_LOGIN_ATTEMPTS == {}

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
        object.__setattr__(settings, 'DEBUG', False)
        response = await client.post(
            "/api/auth/reset-rate-limit",
            headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Rate limit reset is only available in development mode" in response.json()["detail"]
    finally:
        object.__setattr__(settings, "DEBUG", original_debug)
        object.__setattr__(settings, "RATE_LIMIT_RESET_TOKEN", original_token)

@pytest.mark.asyncio
async def test_reset_all_rate_limits_security(client: AsyncClient):
    """Test security for reset-all endpoint"""
    original_debug = settings.DEBUG
    original_token = settings.RATE_LIMIT_RESET_TOKEN
    object.__setattr__(settings, "DEBUG", True)
    object.__setattr__(settings, "RATE_LIMIT_RESET_TOKEN", "dev-reset-token")

    try:
        # Success
        auth_api._FAILED_LOGIN_ATTEMPTS["admin@bijmantra.org"] = {"count": 5, "locked_until": None}
        response = await client.post(
            "/api/auth/reset-all-rate-limits",
            headers={"X-RateLimit-Reset-Token": "dev-reset-token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert auth_api._FAILED_LOGIN_ATTEMPTS == {}

        # Fail
        response = await client.post(
            "/api/auth/reset-all-rate-limits",
            headers={"X-RateLimit-Reset-Token": "wrong"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        object.__setattr__(settings, "DEBUG", original_debug)
        object.__setattr__(settings, "RATE_LIMIT_RESET_TOKEN", original_token)


def test_failed_login_lock_key_is_normalized() -> None:
    auth_api._FAILED_LOGIN_ATTEMPTS.clear()

    auth_api._record_failed_login(" Admin@BijMantra.Org ")

    assert "admin@bijmantra.org" in auth_api._FAILED_LOGIN_ATTEMPTS
    auth_api._clear_failed_login("admin@bijmantra.org")
    assert auth_api._FAILED_LOGIN_ATTEMPTS == {}
