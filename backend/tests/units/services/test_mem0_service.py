from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.modules.ai.services.mem0_service import (
    Mem0ConfigurationError,
    Mem0Service,
)


@pytest.fixture
def restore_mem0_settings(monkeypatch):
    original = {
        "MEM0_ENABLED": settings.MEM0_ENABLED,
        "MEM0_API_KEY": settings.MEM0_API_KEY,
        "MEM0_HOST": settings.MEM0_HOST,
        "MEM0_ORG_ID": settings.MEM0_ORG_ID,
        "MEM0_PROJECT_ID": settings.MEM0_PROJECT_ID,
    }

    yield

    for name, value in original.items():
        monkeypatch.setattr(settings, name, value, raising=False)


def test_mem0_service_status_reflects_settings(monkeypatch, restore_mem0_settings):
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)
    monkeypatch.setattr(settings, "MEM0_HOST", "https://api.mem0.ai", raising=False)
    monkeypatch.setattr(settings, "MEM0_ORG_ID", "org-123", raising=False)
    monkeypatch.setattr(settings, "MEM0_PROJECT_ID", "project-456", raising=False)

    service = Mem0Service()

    assert service.status() == {
        "enabled": True,
        "configured": True,
        "host": "https://api.mem0.ai",
        "org_project_pair_valid": True,
        "project_scoped": True,
    }


@pytest.mark.asyncio
async def test_mem0_service_search_uses_async_client_factory(monkeypatch, restore_mem0_settings):
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)
    monkeypatch.setattr(settings, "MEM0_HOST", "https://memory.example", raising=False)
    monkeypatch.setattr(settings, "MEM0_ORG_ID", "org-123", raising=False)
    monkeypatch.setattr(settings, "MEM0_PROJECT_ID", "project-456", raising=False)

    client = SimpleNamespace(
        search=AsyncMock(return_value={"results": [{"memory": "prefers millet"}]}),
        add=AsyncMock(),
        async_client=SimpleNamespace(aclose=AsyncMock()),
    )
    factory_kwargs: dict[str, object] = {}

    def client_factory(**kwargs):
        factory_kwargs.update(kwargs)
        return client

    service = Mem0Service(client_factory=client_factory)

    result = await service.search(
        "What crop does this user prefer?",
        user_id="user-1",
        agent_id="reevu",
        app_id="bijmantra-dev",
        run_id="session-1",
        limit=3,
        filters={"domain": "preferences"},
    )

    assert result == {"results": [{"memory": "prefers millet"}]}
    assert factory_kwargs == {
        "api_key": "m0-test",
        "host": "https://memory.example",
        "org_id": "org-123",
        "project_id": "project-456",
    }
    client.search.assert_awaited_once_with(
        "What crop does this user prefer?",
        user_id="user-1",
        agent_id="reevu",
        app_id="bijmantra-dev",
        run_id="session-1",
        top_k=3,
        filters={"domain": "preferences"},
    )


@pytest.mark.asyncio
async def test_mem0_service_add_messages_forwards_app_id(monkeypatch, restore_mem0_settings):
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)

    client = SimpleNamespace(
        add=AsyncMock(return_value={"results": [{"id": "mem-1"}]}),
        search=AsyncMock(),
        async_client=SimpleNamespace(aclose=AsyncMock()),
    )

    service = Mem0Service(client_factory=lambda **_: client)

    result = await service.add_messages(
        "Remember the current lane boundary.",
        user_id="user-1",
        agent_id="developer-control-plane",
        app_id="bijmantra-dev",
        run_id="session-1",
        metadata={"category": "note"},
    )

    assert result == {"results": [{"id": "mem-1"}]}
    client.add.assert_awaited_once_with(
        "Remember the current lane boundary.",
        user_id="user-1",
        agent_id="developer-control-plane",
        app_id="bijmantra-dev",
        run_id="session-1",
        metadata={"category": "note"},
    )


@pytest.mark.asyncio
async def test_mem0_service_health_check_uses_search_probe(monkeypatch, restore_mem0_settings):
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)

    client = SimpleNamespace(
        add=AsyncMock(),
        search=AsyncMock(return_value={"results": []}),
        async_client=SimpleNamespace(aclose=AsyncMock()),
    )

    service = Mem0Service(client_factory=lambda **_: client)

    result = await service.health_check(
        user_id="health-user",
        agent_id="developer-control-plane",
        app_id="bijmantra-dev",
        run_id="probe-1",
    )

    assert result["reachable"] is True
    assert result["result_count"] == 0
    assert result["latency_ms"] >= 0
    assert result["detail"] == "Mem0 cloud probe succeeded with the configured backend credentials."
    client.search.assert_awaited_once_with(
        "__developer_mem0_health_probe__",
        user_id="health-user",
        agent_id="developer-control-plane",
        app_id="bijmantra-dev",
        run_id="probe-1",
        top_k=1,
        filters=None,
    )


def test_mem0_service_requires_org_and_project_together(monkeypatch, restore_mem0_settings):
    monkeypatch.setattr(settings, "MEM0_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MEM0_API_KEY", "m0-test", raising=False)
    monkeypatch.setattr(settings, "MEM0_ORG_ID", "org-123", raising=False)
    monkeypatch.setattr(settings, "MEM0_PROJECT_ID", None, raising=False)

    service = Mem0Service(client_factory=lambda **_: object())

    with pytest.raises(Mem0ConfigurationError, match="must be configured together"):
        service._build_client()