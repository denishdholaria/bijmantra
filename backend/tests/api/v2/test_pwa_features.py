import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# PWA Notifications Tests

@pytest.mark.asyncio
async def test_pwa_subscribe_unauthorized(client: AsyncClient):
    """Test that subscribe endpoint requires authentication."""
    response = await client.post("/api/v2/pwa/notifications/subscribe", json={
        "endpoint": "https://example.com/push",
        "keys": {"p256dh": "key", "auth": "secret"}
    })
    # 401 Unauthorized because depends on get_current_user
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pwa_subscribe_success(authenticated_client: AsyncClient):
    """Test successful subscription."""
    payload = {
        "endpoint": "https://example.com/push/123",
        "keys": {"p256dh": "key", "auth": "secret"}
    }
    response = await authenticated_client.post("/api/v2/pwa/notifications/subscribe", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "subscribed"
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_pwa_list_subscriptions(authenticated_client: AsyncClient):
    """Test listing subscriptions."""
    response = await authenticated_client.get("/api/v2/pwa/notifications/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "subscriptions" in data


@pytest.mark.asyncio
async def test_pwa_dispatch_notification(authenticated_client: AsyncClient):
    """Test dispatching a notification."""
    # Ensure at least one subscription exists
    await authenticated_client.post("/api/v2/pwa/notifications/subscribe", json={
        "endpoint": "https://example.com/push/dispatch-test",
        "keys": {"p256dh": "key", "auth": "secret"}
    })

    payload = {
        "title": "Test Notification",
        "body": "This is a test.",
        "data": {"url": "/home"}
    }
    response = await authenticated_client.post("/api/v2/pwa/notifications/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["targets"] >= 1


# PWA Sync Tests

@pytest.mark.asyncio
async def test_pwa_sync_unauthorized(client: AsyncClient):
    """Test that sync endpoint requires authentication."""
    # Note: Using post with json data
    response = await client.post("/api/v2/pwa/drafts/sync", json={
        "drafts": [{"type": "test", "data": {}}]
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pwa_sync_success(authenticated_client: AsyncClient):
    """Test successful draft sync."""
    payload = {
        "drafts": [
            {"type": "observation", "data": {"value": 10}},
            {"type": "note", "data": {"text": "Field visit"}}
        ]
    }
    response = await authenticated_client.post("/api/v2/pwa/drafts/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 2
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_pwa_sync_empty(authenticated_client: AsyncClient):
    """Test sync with empty payload."""
    payload = {"drafts": []}
    response = await authenticated_client.post("/api/v2/pwa/drafts/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 0
    assert data["status"] == "no_content"
