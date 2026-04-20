import json
import hashlib
import hmac
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.modules.core.services.infra.marketplace_webhook_dispatcher import MarketplaceWebhookDispatcher, WebhookPayload
from app.modules.core.services.event_bus import EventBus, EventType

# Import the router to test
from app.api.v2.new_routers.marketplace import router
from fastapi import FastAPI

# Create a TestClient instance for the isolated router
app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestMarketplaceWebhookDispatcher:
    def test_verify_signature_valid(self):
        d = MarketplaceWebhookDispatcher(secret="test_secret")
        payload = b'{"event_type": "integration.connected", "data": {}}'
        signature = hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()
        assert d.verify_signature(payload, signature)

    def test_verify_signature_invalid(self):
        d = MarketplaceWebhookDispatcher(secret="test_secret")
        payload = b'{"event_type": "integration.connected", "data": {}}'
        signature = "invalid_signature"
        assert not d.verify_signature(payload, signature)

    def test_verify_signature_missing(self):
        d = MarketplaceWebhookDispatcher(secret="test_secret")
        payload = b'{"event_type": "integration.connected", "data": {}}'
        assert not d.verify_signature(payload, None)

    @pytest.mark.asyncio
    async def test_dispatch(self):
        mock_event_bus = AsyncMock(spec=EventBus)
        d = MarketplaceWebhookDispatcher(secret="test_secret", event_bus_instance=mock_event_bus)

        await d.dispatch("integration.connected", {"test": "data"})

        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args.kwargs['event_type'] == EventType.INTEGRATION_CONNECTED
        assert call_args.kwargs['data']['original_type'] == "integration.connected"
        assert call_args.kwargs['data']['test'] == "data"
        assert call_args.kwargs['source'] == "marketplace_webhook"

# Dependency override for integration tests
@pytest.fixture
def mock_dispatcher():
    mock_event_bus = AsyncMock(spec=EventBus)
    d = MarketplaceWebhookDispatcher(secret="test_secret", event_bus_instance=mock_event_bus)
    return d

@pytest.fixture
def override_dependency(mock_dispatcher):
    # Override the dependency in the router via dependency_overrides on the app inside TestClient?
    # No, TestClient(router) creates an app. We need to access it.
    # But TestClient wraps the app.
    # The correct way with TestClient(router) is tricky because router is mounted.
    # Actually, TestClient(router) creates a FastAPI app and includes the router.
    # So we can override on client.app.dependency_overrides.

    from app.modules.core.services.infra.marketplace_webhook_dispatcher import dispatcher

    # We need to override the dependency that returns the dispatcher.
    # In api/v2/new_routers/marketplace.py:
    # webhook_dispatcher: MarketplaceWebhookDispatcher = Depends(lambda: dispatcher)

    # We can't easily target the lambda.
    # But we can override `dispatcher` via monkeypatching the module attribute before the test runs,
    # OR we can try to override the dependency using the exact same lambda if we can reference it,
    # which is hard.

    # Easier: Monkeypatch the `dispatcher` instance in the module.
    import app.api.v2.new_routers.marketplace as marketplace_module
    original_dispatcher = marketplace_module.dispatcher
    marketplace_module.dispatcher = mock_dispatcher
    yield
    marketplace_module.dispatcher = original_dispatcher

def test_webhook_endpoint_success(mock_dispatcher, override_dependency):
    payload = {"event_type": "integration.connected", "data": {"id": "123"}}
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(b"test_secret", payload_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/marketplace/webhook",
        content=payload_bytes,
        headers={"X-Marketplace-Signature": signature, "Content-Type": "application/json"}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "event_id": "123"}

    # Verify dispatch was called
    mock_dispatcher.event_bus.publish.assert_called_once()

def test_webhook_endpoint_invalid_signature(mock_dispatcher, override_dependency):
    payload = {"event_type": "integration.connected", "data": {}}
    payload_bytes = json.dumps(payload).encode()
    signature = "invalid"

    response = client.post(
        "/marketplace/webhook",
        content=payload_bytes,
        headers={"X-Marketplace-Signature": signature, "Content-Type": "application/json"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

def test_webhook_endpoint_missing_signature(mock_dispatcher, override_dependency):
    payload = {"event_type": "integration.connected", "data": {}}
    payload_bytes = json.dumps(payload).encode()

    response = client.post(
        "/marketplace/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing signature"

def test_webhook_endpoint_malformed_json(mock_dispatcher, override_dependency):
    payload_bytes = b"invalid json"
    signature = hmac.new(b"test_secret", payload_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/marketplace/webhook",
        content=payload_bytes,
        headers={"X-Marketplace-Signature": signature, "Content-Type": "application/json"}
    )

    assert response.status_code == 400
    # Detail might be "Invalid JSON payload" or specific pydantic error if parsed manually
    assert "Invalid JSON payload" in response.json()["detail"]

def test_webhook_endpoint_missing_event_type(mock_dispatcher, override_dependency):
    payload = {"data": {}}
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(b"test_secret", payload_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/marketplace/webhook",
        content=payload_bytes,
        headers={"X-Marketplace-Signature": signature, "Content-Type": "application/json"}
    )

    # Pydantic validation error or manual check
    assert response.status_code == 400
    # Depending on pydantic version and error handling, it might be "Field required" or "Missing event_type"
    # In my implementation, I catch validation errors and wrap them.
    assert "event_type" in str(response.json()["detail"]) or "Missing event_type" in str(response.json()["detail"])
