import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.api.v2.chat import _derive_routing_decisions, _extract_function_response_message
from app.modules.ai.services.reevu import ReevuMetrics


class FakeMultiTierLLMService:
    instances: list["FakeMultiTierLLMService"] = []

    def __init__(self):
        self.registry = None
        self.chat_calls: list[dict] = []
        self.stream_calls: list[dict] = []
        self.__class__.instances.append(self)

    def set_provider_registry(self, registry_to_apply):
        self.registry = registry_to_apply

    def get_routing_state(self):
        return getattr(
            self.registry,
            "routing_state",
            {
                "preferred_provider": None,
                "preferred_provider_only": False,
                "selection_mode": "priority_order",
            },
        )

    async def get_status(self):
        if self.registry is None:
            return {
                "active_provider": "template",
                "active_model": "template-v1",
                "providers": {
                    "template": {"available": True, "free_tier": True},
                },
            }

        return {
            "active_provider": self.registry.active_provider,
            "active_model": self.registry.active_model,
            "active_provider_source": getattr(self.registry, "active_provider_source", "server_env"),
            "active_provider_source_label": getattr(self.registry, "active_provider_source_label", "Server env key"),
            "providers": self.registry.providers,
        }

    async def chat(
        self,
        *,
        user_message,
        conversation_history,
        context,
        preferred_provider=None,
        organization_id=None,
        user_id=None,
        user_api_key=None,
        user_model=None,
        system_prompt_override=None,
        prompt_mode_capabilities=None,
    ):
        provider_name = preferred_provider.value if preferred_provider else self.registry.active_provider
        model_name = user_model or self.registry.model_by_provider.get(provider_name, self.registry.active_model)
        self.chat_calls.append(
            {
                "user_message": user_message,
                "conversation_history": conversation_history,
                "context": context,
                "preferred_provider": preferred_provider,
                "organization_id": organization_id,
                "user_id": user_id,
                "user_api_key": user_api_key,
                "user_model": user_model,
                "system_prompt_override": system_prompt_override,
                "prompt_mode_capabilities": prompt_mode_capabilities,
            }
        )
        return SimpleNamespace(
            content=f"Scoped response via {provider_name}",
            provider=SimpleNamespace(value=provider_name),
            model=model_name,
            model_confirmed=True,
            cached=False,
            latency_ms=12.5,
        )

    async def stream_chat(
        self,
        *,
        user_message,
        conversation_history=None,
        context=None,
        preferred_provider=None,
        user_api_key=None,
        user_model=None,
        system_prompt_override=None,
        prompt_mode_capabilities=None,
    ):
        provider_name = preferred_provider.value if preferred_provider else self.registry.active_provider
        self.stream_calls.append(
            {
                "user_message": user_message,
                "conversation_history": conversation_history,
                "context": context,
                "preferred_provider": preferred_provider,
                "user_api_key": user_api_key,
                "user_model": user_model,
                "system_prompt_override": system_prompt_override,
                "prompt_mode_capabilities": prompt_mode_capabilities,
            }
        )
        yield f"Streamed response via {provider_name}"
        yield " with telemetry"


def _build_registry(
    active_provider="openai",
    active_model="gpt-4.1-mini",
    *,
    include_free_tier=True,
    active_provider_source: str = "server_env",
    active_provider_source_label: str = "Server env key",
    preferred_provider: str | None = None,
    preferred_provider_only: bool = False,
):
    providers = {
        "openai": {"available": True, "free_tier": False, "source": active_provider_source, "source_label": active_provider_source_label},
        "template": {"available": True, "free_tier": True, "source": "template_builtin", "source_label": "Built-in template fallback"},
    }
    if include_free_tier:
        providers["groq"] = {"available": True, "free_tier": True, "source": "server_env", "source_label": "Server env key"}

    selection_mode = "priority_order"
    if preferred_provider and preferred_provider_only:
        selection_mode = "preferred_only"
    elif preferred_provider:
        selection_mode = "preferred_with_fallback"

    return SimpleNamespace(
        active_provider=active_provider,
        active_model=active_model,
        active_provider_source=active_provider_source,
        active_provider_source_label=active_provider_source_label,
        providers=providers,
        routing_state={
            "preferred_provider": preferred_provider,
            "preferred_provider_only": preferred_provider_only,
            "selection_mode": selection_mode,
        },
        model_by_provider={
            "openai": "gpt-4.1-mini",
            "groq": "llama-4-scout",
            "template": "template-v1",
        },
    )


@pytest.fixture
def client():
    from app.api.deps import get_current_user, get_db
    from app.api.v2.chat import get_breeding_service, get_reevu_service
    from app.main import app

    reevu_service = SimpleNamespace(
        get_or_create_user_context=AsyncMock(return_value={"context": "ok"}),
        update_interaction_stats=AsyncMock(return_value=None),
        save_episodic_memory=AsyncMock(return_value=None),
    )
    breeding_service = SimpleNamespace(search_breeding_knowledge=AsyncMock(return_value=[]))
    db_session = SimpleNamespace(name="db-session")

    async def override_current_user():
        return SimpleNamespace(
            id=1,
            organization_id=1,
            email="test@bijmantra.org",
            is_demo=False,
            is_superuser=False,
        )

    async def override_get_db():
        yield db_session

    async def override_reevu_service():
        return reevu_service

    async def override_breeding_service():
        return breeding_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_reevu_service] = override_reevu_service
    app.dependency_overrides[get_breeding_service] = override_breeding_service

    with TestClient(app) as test_client:
        yield test_client, db_session

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_chat_infra():
    FakeMultiTierLLMService.instances.clear()
    ReevuMetrics.reset()
    with patch("app.api.v2.chat.AIQuotaService.check_and_increment_usage", new=AsyncMock(return_value=None)) as mock_quota, patch(
        "app.api.v2.chat.AIQuotaService.record_generation_usage",
        new=AsyncMock(return_value=None),
    ) as mock_usage_telemetry, patch(
        "app.api.v2.chat.FunctionCallingService.detect_function_call",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.api.v2.chat._validate_response_content",
        return_value=(
            SimpleNamespace(valid=True, errors=[]),
            SimpleNamespace(evidence_refs=set(), calculation_ids=set()),
        ),
    ), patch(
        "app.api.v2.chat._build_reevu_envelope",
        return_value={"evidence_refs": [], "calculations": [], "uncertainty": [], "policy_flags": []},
    ):
        yield {"quota": mock_quota, "usage_telemetry": mock_usage_telemetry}


def test_chat_route_uses_request_scoped_registry_metadata(client):
    test_client, db_session = client
    registry = _build_registry()
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["model_confirmed"] is True
    provider_service.load_registry.assert_awaited_once()
    assert provider_service.load_registry.await_args.args == (db_session, 1)
    assert provider_service.load_registry.await_args.kwargs == {"is_superuser": False}


def test_extract_function_response_message_uses_comparison_context_message():
    message = _extract_function_response_message(
        {
            "comparison_context": {
                "message": "Compared 2 germplasm entries using the shared phenotype interpretation contract",
            }
        }
    )

    assert message == "Compared 2 germplasm entries using the shared phenotype interpretation contract"


def test_extract_function_response_message_builds_safe_failure_message_when_message_missing():
    message = _extract_function_response_message(
        {
            "success": False,
            "error": "Ambiguous trial query",
            "safe_failure": {
                "error_category": "ambiguous_retrieval_scope",
                "searched": ["trial_summary", "trial_search_service"],
                "missing": ["single authoritative trial match"],
                "next_steps": ["Retry with the exact trial ID."],
            },
        }
    )

    assert message == (
        "Ambiguous trial query. "
        "Missing grounded input: single authoritative trial match. "
        "Next step: Retry with the exact trial ID."
    )


def test_chat_route_honors_preferred_provider_and_byok(client, mock_chat_infra):
    test_client, _ = client
    registry = _build_registry()
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    base_service = FakeMultiTierLLMService()

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=base_service
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post(
            "/api/v2/chat",
            json={
                "message": "Hello",
                "include_context": False,
                "preferred_provider": "groq",
                "user_api_key": "user-key",
                "user_model": "llama-4-scout",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "groq"
    assert payload["model"] == "llama-4-scout"
    resolved_service = FakeMultiTierLLMService
    assert resolved_service is not None
    chat_call = base_service.chat_calls[0] if base_service.chat_calls else None
    assert chat_call is None
    assert mock_chat_infra["quota"].await_count == 0


def test_chat_route_records_token_telemetry_for_managed_requests(client, mock_chat_infra):
    test_client, db_session = client
    registry = _build_registry()
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    async def chat_with_tokens(self, **kwargs):
        return SimpleNamespace(
            content="Scoped response via openai",
            provider=SimpleNamespace(value="openai"),
            model="gpt-4.1-mini",
            model_confirmed=True,
            tokens_used=165,
            input_tokens=120,
            output_tokens=45,
            cached=False,
            latency_ms=12.5,
        )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch.object(
        FakeMultiTierLLMService,
        "chat",
        chat_with_tokens,
    ):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    usage_call = mock_chat_infra["usage_telemetry"].await_args
    assert usage_call.args == (db_session, 1)
    assert usage_call.kwargs == {"tokens_input": 120, "tokens_output": 45}


def test_usage_route_returns_richer_telemetry_payload(client):
    test_client, db_session = client
    registry = _build_registry(
        active_provider="openai",
        active_model="gpt-4.1-mini",
        active_provider_source="organization_config",
        active_provider_source_label="Organization AI settings",
    )
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    usage_payload = {
        "used": 42,
        "limit": 50,
        "remaining": 8,
        "request_percentage_used": 84.0,
        "quota_authority": "request_count",
        "provider": {
            "active_provider": "openai",
            "active_model": "gpt-4.1-mini",
            "active_provider_source": "organization_config",
            "active_provider_source_label": "Organization AI settings",
        },
        "token_telemetry": {
            "input_tokens": 2100,
            "output_tokens": 540,
            "total_tokens": 2640,
            "coverage_state": "supplemental",
            "coverage_message": "Token telemetry is supplemental only. Request-count quota remains the enforcement authority for this slice.",
        },
        "attribution": {
            "lane": {
                "supported": False,
                "value": None,
                "reason": "Lane attribution is not linked from the canonical REEVU chat request path yet.",
            },
            "mission": {
                "supported": False,
                "value": None,
                "reason": "Mission attribution is not linked from the canonical REEVU chat request path yet.",
            },
        },
        "soft_alert": {
            "state": "watch",
            "threshold_basis": "request_count",
            "percent_used": 84.0,
            "message": "Quota pressure is rising. Plan managed usage carefully.",
        },
    }

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
        "app.api.v2.chat.AIQuotaService.get_usage_stats",
        new=AsyncMock(return_value=usage_payload),
    ) as mock_get_usage:
        response = test_client.get("/api/v2/chat/usage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["used"] == 42
    assert payload["provider"]["active_provider"] == "openai"
    assert payload["provider"]["active_provider_source_label"] == "Organization AI settings"
    assert payload["token_telemetry"]["total_tokens"] == 2640
    assert payload["soft_alert"]["state"] == "watch"
    assert payload["attribution"]["lane"]["supported"] is False

    usage_call = mock_get_usage.await_args
    assert usage_call.args == (db_session, 1)
    assert usage_call.kwargs["provider_status"]["active_provider"] == "openai"


@pytest.mark.parametrize(
    ("organization_id", "is_superuser"),
    [
        (1, False),
        (7, False),
        (19, True),
    ],
)
def test_status_route_loads_registry_with_current_org(organization_id, is_superuser):
    from app.api.deps import get_current_user, get_db
    from app.main import app

    registry = _build_registry()
    provider_service = SimpleNamespace(load_registry=AsyncMock(return_value=registry))
    db_session = SimpleNamespace(name=f"db-{organization_id}")

    async def override_current_user():
        return SimpleNamespace(
            id=organization_id,
            organization_id=organization_id,
            email=f"org-{organization_id}@bijmantra.org",
            is_demo=False,
            is_superuser=is_superuser,
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client, patch(
        "app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService
    ), patch("app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()), patch(
        "app.api.v2.chat.get_ai_provider_service", return_value=provider_service
    ):
        response = test_client.get("/api/v2/chat/status")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "openai"
    assert payload["active_model"] == "gpt-4.1-mini"
    assert payload["active_provider_source"] == "server_env"
    assert payload["active_provider_source_label"] == "Server env key"
    provider_service.load_registry.assert_awaited_once()
    assert provider_service.load_registry.await_args.args == (db_session, organization_id)
    assert provider_service.load_registry.await_args.kwargs == {"is_superuser": is_superuser}


def test_health_route_reflects_request_scoped_provider_and_free_tier(client):
    test_client, _ = client
    registry = _build_registry(active_provider="openai", active_model="gpt-4.1-mini", include_free_tier=True)
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.get("/api/v2/chat/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "openai"
    assert payload["active_model"] == "gpt-4.1-mini"
    assert payload["active_provider_source"] == "server_env"
    assert payload["active_provider_source_label"] == "Server env key"
    assert payload["llm_enabled"] is True
    assert payload["free_tier_available"] is True


def test_health_route_reports_template_fallback_when_registry_defaults_to_template(client):
    test_client, _ = client
    registry = _build_registry(
        active_provider="template",
        active_model="template-v1",
        include_free_tier=False,
        active_provider_source="template_builtin",
        active_provider_source_label="Built-in template fallback",
    )
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.get("/api/v2/chat/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "template"
    assert payload["active_model"] == "template-v1"
    assert payload["active_provider_source"] == "template_builtin"
    assert payload["active_provider_source_label"] == "Built-in template fallback"
    assert payload["llm_enabled"] is False
    assert payload["free_tier_available"] is True


def test_chat_route_filters_function_manifest_using_agent_capabilities(client):
    test_client, _ = client
    registry = _build_registry()
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(
            return_value=SimpleNamespace(
                capability_overrides=["search_trials"],
                tool_policy=None,
            )
        ),
    )

    class RecordingFunctionCallingService:
        instances: list["RecordingFunctionCallingService"] = []

        def __init__(self, api_key=None, function_schemas=None):
            self.function_schemas = function_schemas or []
            self.__class__.instances.append(self)

        async def detect_function_call(self, user_message, conversation_history=None):
            return None

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
        "app.api.v2.chat.FunctionCallingService", RecordingFunctionCallingService
    ):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    assert RecordingFunctionCallingService.instances
    function_names = [
        function_schema["name"]
        for function_schema in RecordingFunctionCallingService.instances[-1].function_schemas
    ]
    assert function_names == ["search_trials"]
    provider_service.get_agent_setting.assert_awaited_once()


def test_chat_route_passes_prompt_modes_from_agent_setting(client):
    test_client, _ = client
    registry = _build_registry()
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(
            return_value=SimpleNamespace(
                capability_overrides=None,
                tool_policy=None,
                prompt_mode_capabilities=["breeding_mode", "genomics_mode"],
                system_prompt_override=None,
            )
        ),
    )
    base_service = FakeMultiTierLLMService()

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=base_service
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    resolved_service = FakeMultiTierLLMService.instances[-1]
    assert resolved_service.chat_calls[0]["prompt_mode_capabilities"] == ["breeding_mode", "genomics_mode"]


@pytest.mark.parametrize(
    ("requested_provider", "actual_provider", "routing_state", "expected"),
    [
        (
            "GROQ",
            "groq",
            None,
            ["request_override", "request_override_applied"],
        ),
        (
            "groq",
            "template",
            None,
            ["request_override", "request_override_fallback", "template_fallback"],
        ),
        (
            None,
            "openai",
            None,
            ["priority_order"],
        ),
        (
            None,
            "openai",
            {
                "preferred_provider": "openai",
                "preferred_provider_only": True,
                "selection_mode": "preferred_only",
            },
            ["managed_preferred_only", "managed_preferred_hit"],
        ),
        (
            None,
            "template",
            {
                "preferred_provider": "openai",
                "preferred_provider_only": False,
                "selection_mode": "preferred_with_fallback",
            },
            ["managed_preferred", "managed_preferred_miss", "template_fallback"],
        ),
    ],
)
def test_derive_routing_decisions_covers_expected_paths(
    requested_provider,
    actual_provider,
    routing_state,
    expected,
):
    assert _derive_routing_decisions(
        requested_provider=requested_provider,
        actual_provider=actual_provider,
        routing_state=routing_state,
    ) == expected


@pytest.mark.parametrize(
    ("registry", "payload", "expected_provider", "expected_decisions"),
    [
        (
            _build_registry(active_provider="openai", active_model="gpt-4.1-mini"),
            {"message": "Hello", "include_context": False},
            "openai",
            ["priority_order"],
        ),
        (
            _build_registry(
                active_provider="openai",
                active_model="gpt-4.1-mini",
                preferred_provider="openai",
                preferred_provider_only=False,
            ),
            {"message": "Hello", "include_context": False},
            "openai",
            ["managed_preferred", "managed_preferred_hit"],
        ),
        (
            _build_registry(active_provider="openai", active_model="gpt-4.1-mini"),
            {"message": "Hello", "include_context": False, "preferred_provider": "groq"},
            "groq",
            ["request_override", "request_override_applied"],
        ),
    ],
)
def test_chat_route_records_routing_decisions_in_metrics(
    client,
    registry,
    payload,
    expected_provider,
    expected_decisions,
):
    test_client, _ = client
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post("/api/v2/chat", json=payload)

    assert response.status_code == 200
    assert response.json()["provider"] == expected_provider

    diagnostics = ReevuMetrics.get().get_diagnostics_snapshot()
    routing_decisions = {
        item["decision"]: item["count"]
        for item in diagnostics["routing_decisions"]
    }
    request_statuses = {
        item["status"]: item["count"]
        for item in diagnostics["request_statuses"]
    }

    assert request_statuses == {"ok": 1}
    for decision in expected_decisions:
        assert routing_decisions[decision] == 1


def test_chat_route_emits_request_trace_for_regular_sync_path(client):
    test_client, _ = client
    registry = _build_registry(active_provider="openai", active_model="gpt-4.1-mini")
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["request_id"], str)
    assert payload["retrieval_audit"] == {"services": [], "entities": {"query": "Hello"}}
    assert isinstance(payload["plan_execution_summary"]["plan_id"], str)
    assert payload["plan_execution_summary"]["total_steps"] == len(
        payload["plan_execution_summary"]["steps"]
    )

    primary_domain = payload["plan_execution_summary"]["domains_involved"][0]
    diagnostics = ReevuMetrics.get().get_diagnostics_snapshot()
    assert diagnostics["retrieval_execution"] == {
        "traced_requests": 1,
        "compound_requests": 0,
        "functions": [],
        "domains": [{"domain": primary_domain, "count": 1}],
        "services": [],
    }


def test_function_chat_route_records_retrieval_execution_in_metrics(client):
    test_client, _ = client
    registry = _build_registry(active_provider="openai", active_model="gpt-4.1-mini")
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    function_call = SimpleNamespace(
        name="search_trials",
        parameters={"crop": "rice"},
        to_dict=lambda: {"name": "search_trials", "parameters": {"crop": "rice"}},
    )

    async def mock_detect_function_call(*args, **kwargs):
        return function_call

    async def mock_execute(*args, **kwargs):
        return {
            "success": True,
            "function": "search_trials",
            "result_type": "result",
            "data": {"total": 2},
            "retrieval_audit": {
                "services": ["trial_search_service.search"],
                "entities": {"crop": "rice"},
            },
        }

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
        "app.api.v2.chat.FunctionCallingService.detect_function_call",
        side_effect=mock_detect_function_call,
    ), patch(
        "app.api.v2.chat.FunctionExecutor.execute",
        side_effect=mock_execute,
    ):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Show rice trials", "include_context": False},
        )

    assert response.status_code == 200
    payload = response.json()
    primary_domain = payload["plan_execution_summary"]["domains_involved"][0]
    assert isinstance(payload["request_id"], str)
    assert payload["retrieval_audit"] == {
        "services": ["trial_search_service.search"],
        "entities": {"crop": "rice"},
    }
    assert payload["plan_execution_summary"]["total_steps"] == len(
        payload["plan_execution_summary"]["steps"]
    )

    diagnostics = ReevuMetrics.get().get_diagnostics_snapshot()
    request_statuses = {
        item["status"]: item["count"]
        for item in diagnostics["request_statuses"]
    }

    assert request_statuses == {"ok": 1}
    retrieval_execution = diagnostics["retrieval_execution"]
    assert retrieval_execution["traced_requests"] == 1
    assert retrieval_execution["compound_requests"] == int(
        payload["plan_execution_summary"]["is_compound"]
    )
    assert retrieval_execution["functions"] == [{"function_name": "search_trials", "count": 1}]
    assert retrieval_execution["services"] == [{"service": "trial_search_service.search", "count": 1}]
    assert {item["domain"] for item in retrieval_execution["domains"]} == set(
        payload["plan_execution_summary"]["domains_involved"]
    )


def test_chat_route_injects_current_organization_into_function_execution(client):
    test_client, _ = client
    from app.api.deps import get_current_user
    from app.main import app

    registry = _build_registry(active_provider="openai", active_model="gpt-4.1-mini")
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    function_call = SimpleNamespace(
        name="get_germplasm_details",
        parameters={"query": "IR64"},
        to_dict=lambda: {"name": "get_germplasm_details", "parameters": {"query": "IR64"}},
    )
    captured: dict[str, object] = {}

    async def override_current_user():
        return SimpleNamespace(
            id=7,
            organization_id=7,
            email="org-7@bijmantra.org",
            is_demo=False,
            is_superuser=False,
        )

    async def mock_detect_function_call(*args, **kwargs):
        return function_call

    async def mock_execute(*args, **kwargs):
        function_name, parameters = args[-2:]
        captured["function_name"] = function_name
        captured["parameters"] = parameters
        return {
            "success": True,
            "function": "get_germplasm_details",
            "result_type": "germplasm_details",
            "message": "Resolved IR64",
            "retrieval_audit": {
                "services": ["germplasm_search_service.get_by_id"],
                "entities": {"query": "IR64"},
            },
        }

    app.dependency_overrides[get_current_user] = override_current_user

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
        "app.api.v2.chat.FunctionCallingService.detect_function_call",
        side_effect=mock_detect_function_call,
    ), patch(
        "app.api.v2.chat.FunctionExecutor.execute",
        side_effect=mock_execute,
    ):
        response = test_client.post(
            "/api/v2/chat",
            json={"message": "Show the details for germplasm IR64", "include_context": False},
        )

    assert response.status_code == 200
    assert captured["function_name"] == "get_germplasm_details"
    assert captured["parameters"] == {"query": "IR64", "organization_id": 7}


def test_stream_route_records_routing_decisions_in_metrics(client):
    test_client, _ = client
    registry = _build_registry(
        active_provider="openai",
        active_model="gpt-4.1-mini",
        preferred_provider="openai",
        preferred_provider_only=False,
    )
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service):
        response = test_client.post(
            "/api/v2/chat/stream",
            json={"message": "Hello", "include_context": False},
        )

    assert response.status_code == 200
    events = []
    for line in response.text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        with_context = None
        try:
            with_context = json.loads(payload)
        except json.JSONDecodeError:
            continue
        events.append(with_context)

    assert any(event.get("type") == "start" for event in events)
    assert any(event.get("type") == "done" for event in events)

    diagnostics = ReevuMetrics.get().get_diagnostics_snapshot()
    routing_decisions = {
        item["decision"]: item["count"]
        for item in diagnostics["routing_decisions"]
    }
    request_statuses = {
        item["status"]: item["count"]
        for item in diagnostics["request_statuses"]
    }

    assert request_statuses == {"ok": 1}
    assert routing_decisions["managed_preferred"] == 1
    assert routing_decisions["managed_preferred_hit"] == 1


def test_stream_route_injects_current_organization_into_function_execution(client):
    test_client, _ = client
    from app.api.deps import get_current_user
    from app.main import app

    registry = _build_registry(active_provider="openai", active_model="gpt-4.1-mini")
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    function_call = SimpleNamespace(
        name="get_germplasm_details",
        parameters={"query": "IR64"},
        to_dict=lambda: {"name": "get_germplasm_details", "parameters": {"query": "IR64"}},
    )
    captured: dict[str, object] = {}

    async def override_current_user():
        return SimpleNamespace(
            id=7,
            organization_id=7,
            email="org-7@bijmantra.org",
            is_demo=False,
            is_superuser=False,
        )

    async def mock_detect_function_call(*args, **kwargs):
        return function_call

    async def mock_execute(*args, **kwargs):
        function_name, parameters = args[-2:]
        captured["function_name"] = function_name
        captured["parameters"] = parameters
        return {
            "success": True,
            "function": "get_germplasm_details",
            "result_type": "germplasm_details",
            "message": "Resolved IR64",
            "retrieval_audit": {
                "services": ["germplasm_search_service.get_by_id"],
                "entities": {"query": "IR64"},
            },
        }

    app.dependency_overrides[get_current_user] = override_current_user

    with patch("app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService), patch(
        "app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()
    ), patch("app.api.v2.chat.get_ai_provider_service", return_value=provider_service), patch(
        "app.api.v2.chat.FunctionCallingService.detect_function_call",
        side_effect=mock_detect_function_call,
    ), patch(
        "app.api.v2.chat.FunctionExecutor.execute",
        side_effect=mock_execute,
    ):
        response = test_client.post(
            "/api/v2/chat/stream",
            json={"message": "Show the details for germplasm IR64", "include_context": False},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    events = []
    for line in response.text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue

    assert any(event.get("type") == "done" for event in events)
    assert captured["function_name"] == "get_germplasm_details"
    assert captured["parameters"] == {"query": "IR64", "organization_id": 7}


def test_diagnostics_route_returns_provider_latencies_and_safe_failures():
    from app.api.deps import get_current_user, get_db
    from app.main import app

    registry = _build_registry(
        active_provider="openai",
        active_model="gpt-4.1-mini",
        include_free_tier=True,
        preferred_provider="openai",
        preferred_provider_only=False,
    )
    provider_service = SimpleNamespace(
        load_registry=AsyncMock(return_value=registry),
        get_agent_setting=AsyncMock(return_value=None),
    )
    db_session = SimpleNamespace(name="db-superuser")

    async def override_current_user():
        return SimpleNamespace(
            id=99,
            organization_id=1,
            email="admin@bijmantra.org",
            is_demo=False,
            is_superuser=True,
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_get_db

    metrics = ReevuMetrics.get()
    metrics.record_request(
        status="ok",
        latency_seconds=0.25,
        provider="openai",
        routing_decisions=["managed_preferred", "managed_preferred_hit"],
        retrieval_audit={
            "services": ["trial_search_service.search"],
            "entities": {"crop": "rice"},
        },
        plan_execution_summary={
            "domains_involved": ["trials"],
            "is_compound": False,
        },
    )
    metrics.record_request(
        status="safe_failure",
        latency_seconds=0.5,
        provider="template",
        policy_flags=["missing_evidence"],
        safe_failure_reason="insufficient_evidence",
        routing_decisions=["managed_preferred", "managed_preferred_miss", "template_fallback"],
        retrieval_audit={"services": [], "entities": {"query": "Hello"}},
        plan_execution_summary={
            "domains_involved": ["breeding", "weather"],
            "is_compound": True,
        },
    )

    with TestClient(app) as test_client, patch(
        "app.api.v2.chat.MultiTierLLMService", FakeMultiTierLLMService
    ), patch("app.api.v2.chat.get_llm_service", return_value=FakeMultiTierLLMService()), patch(
        "app.api.v2.chat.get_ai_provider_service", return_value=provider_service
    ):
        response = test_client.get("/api/v2/chat/diagnostics")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "openai"
    assert payload["active_model"] == "gpt-4.1-mini"
    assert payload["database_authority"] == {
        "backend": "postgresql",
        "server": "localhost",
        "port": 5432,
        "database": "bijmantra_db",
        "user": "bijmantra_user",
        "url_redacted": "postgresql+asyncpg://bijmantra_user:***@localhost:5432/bijmantra_db",
    }
    assert payload["total_requests"] == 2
    assert payload["providers"][0]["provider"] == "groq"
    assert payload["provider_latencies"] == [
        {"provider": "openai", "count": 1, "p50": 0.25, "p95": None, "p99": None},
        {"provider": "template", "count": 1, "p50": 0.5, "p95": None, "p99": None},
    ]
    assert payload["routing_state"] == {
        "preferred_provider": "openai",
        "preferred_provider_only": False,
        "selection_mode": "preferred_with_fallback",
    }
    assert payload["routing_decisions"] == [
        {"decision": "managed_preferred", "count": 2},
        {"decision": "managed_preferred_hit", "count": 1},
        {"decision": "managed_preferred_miss", "count": 1},
        {"decision": "template_fallback", "count": 1},
    ]
    assert payload["retrieval_execution"] == {
        "traced_requests": 2,
        "compound_requests": 1,
        "functions": [],
        "domains": [
            {"domain": "breeding", "count": 1},
            {"domain": "trials", "count": 1},
            {"domain": "weather", "count": 1},
        ],
        "services": [{"service": "trial_search_service.search", "count": 1}],
    }
    assert payload["safe_failures"] == [{"reason": "insufficient_evidence", "count": 1}]
    assert payload["policy_flags"] == [{"flag": "missing_evidence", "count": 1}]
