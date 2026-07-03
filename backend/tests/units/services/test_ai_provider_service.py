from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.ai_configuration import AIProvider, AIProviderModel, ReevuAgentSetting, ReevuRoutingPolicy
from app.modules.ai.service import AIProviderService
from app.modules.ai.services.provider_types import LLMConfig, LLMProvider


def _build_provider(
    *,
    provider_id: int,
    organization_id: int,
    provider_key: str,
    priority: int,
    api_key: str = "test-key",
    base_url: str | None = None,
) -> AIProvider:
    provider = AIProvider(
        id=provider_id,
        organization_id=organization_id,
        provider_key=provider_key,
        display_name=provider_key.title(),
        priority=priority,
        encrypted_api_key=api_key,
        base_url=base_url,
        is_enabled=True,
        is_byok_allowed=True,
        auth_mode="api_key",
    )
    provider.models = []
    return provider


def _build_model(
    *,
    model_id: int,
    organization_id: int,
    provider: AIProvider,
    model_name: str,
    is_default: bool,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> AIProviderModel:
    model = AIProviderModel(
        id=model_id,
        organization_id=organization_id,
        provider_id=provider.id,
        model_name=model_name,
        display_name=model_name,
        is_default=is_default,
        is_active=True,
        max_tokens=max_tokens,
        temperature=temperature,
        is_streaming_supported=True,
    )
    model.provider = provider
    provider.models.append(model)
    return model


def _build_agent_setting(
    *,
    organization_id: int,
    provider: AIProvider | None = None,
    provider_model: AIProviderModel | None = None,
    sampling_temperature: float | None = None,
    max_tokens: int | None = None,
) -> ReevuAgentSetting:
    setting = ReevuAgentSetting(
        id=900,
        organization_id=organization_id,
        agent_key="reevu",
        provider_id=provider.id if provider else None,
        provider_model_id=provider_model.id if provider_model else None,
        sampling_temperature=sampling_temperature,
        max_tokens=max_tokens,
        is_active=True,
    )
    setting.provider = provider
    setting.provider_model = provider_model
    return setting


def _build_routing_policy(
    *,
    organization_id: int,
    provider: AIProvider | None = None,
    provider_model: AIProviderModel | None = None,
    fallback_to_priority_order: bool = True,
) -> ReevuRoutingPolicy:
    policy = ReevuRoutingPolicy(
        id=901,
        organization_id=organization_id,
        agent_key="reevu",
        preferred_provider_id=provider.id if provider else None,
        preferred_provider_model_id=provider_model.id if provider_model else None,
        fallback_to_priority_order=fallback_to_priority_order,
        is_active=True,
    )
    policy.provider = provider
    policy.provider_model = provider_model
    return policy


@pytest.fixture
def deterministic_registry_defaults(monkeypatch):
    def fake_initialize_from_settings(self):
        self.register(
            LLMProvider.GROQ,
            LLMConfig(
                provider=LLMProvider.GROQ,
                model="groq-default",
                base_url="https://groq.example/v1",
                available=False,
                free_tier=True,
                rate_limit=30,
            ),
        )
        self.register(
            LLMProvider.OLLAMA,
            LLMConfig(
                provider=LLMProvider.OLLAMA,
                model="llama3.2:3b",
                source="local_runtime",
                base_url="http://localhost:11434",
                available=False,
                free_tier=True,
            ),
        )
        self.register(
            LLMProvider.OPENAI,
            LLMConfig(
                provider=LLMProvider.OPENAI,
                model="openai-default",
                base_url="https://openai.example/v1",
                available=False,
                free_tier=False,
                rate_limit=60,
            ),
        )
        self.register(
            LLMProvider.ANTHROPIC,
            LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="anthropic-default",
                base_url="https://anthropic.example/v1",
                available=False,
                free_tier=False,
                rate_limit=60,
            ),
        )
        self.register(
            LLMProvider.TEMPLATE,
            LLMConfig(
                provider=LLMProvider.TEMPLATE,
                model="template-v1",
                available=True,
                free_tier=True,
            ),
        )

    monkeypatch.setattr(
        "app.modules.ai.adapters.provider_registry.ProviderRegistry._initialize_from_settings",
        fake_initialize_from_settings,
    )


@pytest.fixture
def provider_service() -> AIProviderService:
    return AIProviderService()


@pytest.mark.asyncio
async def test_load_registry_returns_env_fallback_when_org_has_no_persisted_providers(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    captured: dict[str, object] = {}

    async def fake_set_tenant_context(db, organization_id, is_superuser=False):
        captured["db"] = db
        captured["organization_id"] = organization_id
        captured["is_superuser"] = is_superuser

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", fake_set_tenant_context)
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[]))

    db = SimpleNamespace(name="db-session")
    registry = await provider_service.load_registry(db, 42, is_superuser=True)

    assert captured == {
        "db": db,
        "organization_id": 42,
        "is_superuser": True,
    }
    assert [config.provider for config in registry.get_available()] == [LLMProvider.TEMPLATE]
    assert registry.get(LLMProvider.OPENAI).available is False


@pytest.mark.asyncio
async def test_load_registry_orders_persisted_providers_by_priority(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    groq = _build_provider(
        provider_id=1,
        organization_id=7,
        provider_key="groq",
        priority=10,
        api_key="groq-key",
    )
    _build_model(
        model_id=11,
        organization_id=7,
        provider=groq,
        model_name="llama-4-scout",
        is_default=True,
    )

    openai = _build_provider(
        provider_id=2,
        organization_id=7,
        provider_key="openai",
        priority=50,
        api_key="openai-key",
    )
    _build_model(
        model_id=21,
        organization_id=7,
        provider=openai,
        model_name="gpt-4.1-mini",
        is_default=True,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[openai, groq]))

    registry = await provider_service.load_registry(SimpleNamespace(), 7)
    available_providers = [config.provider for config in registry.get_available()]

    assert available_providers == [LLMProvider.GROQ, LLMProvider.OPENAI, LLMProvider.TEMPLATE]


@pytest.mark.asyncio
async def test_load_registry_prefers_agent_provider_model_over_priority(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    groq = _build_provider(
        provider_id=1,
        organization_id=9,
        provider_key="groq",
        priority=1,
        api_key="groq-key",
    )
    _build_model(
        model_id=11,
        organization_id=9,
        provider=groq,
        model_name="llama-fast",
        is_default=True,
    )

    openai = _build_provider(
        provider_id=2,
        organization_id=9,
        provider_key="openai",
        priority=99,
        api_key="openai-key",
    )
    openai_model = _build_model(
        model_id=21,
        organization_id=9,
        provider=openai,
        model_name="gpt-4.1",
        is_default=True,
    )
    agent_setting = _build_agent_setting(
        organization_id=9,
        provider_model=openai_model,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=agent_setting))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[groq, openai]))

    registry = await provider_service.load_registry(SimpleNamespace(), 9)
    available = registry.get_available()

    assert len(available) == 1
    assert available[0].provider == LLMProvider.OPENAI
    assert available[0].model == "gpt-4.1"


@pytest.mark.asyncio
async def test_load_registry_applies_agent_token_and_temperature_overrides(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    openai = _build_provider(
        provider_id=4,
        organization_id=5,
        provider_key="openai",
        priority=20,
        api_key="openai-key",
    )
    openai_model = _build_model(
        model_id=41,
        organization_id=5,
        provider=openai,
        model_name="gpt-4.1-mini",
        is_default=True,
        max_tokens=2048,
        temperature=0.2,
    )
    agent_setting = _build_agent_setting(
        organization_id=5,
        provider_model=openai_model,
        sampling_temperature=0.05,
        max_tokens=4096,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=agent_setting))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[openai]))

    registry = await provider_service.load_registry(SimpleNamespace(), 5)
    config = registry.get(LLMProvider.OPENAI)

    assert config is not None
    assert config.model == "gpt-4.1-mini"
    assert config.temperature == pytest.approx(0.05)
    assert config.max_tokens == 4096
    assert config.available is True


@pytest.mark.asyncio
async def test_load_registry_uses_model_defaults_for_non_targeted_providers(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    anthropic = _build_provider(
        provider_id=1,
        organization_id=12,
        provider_key="anthropic",
        priority=30,
        api_key="anthropic-key",
    )
    anthropic_model = _build_model(
        model_id=11,
        organization_id=12,
        provider=anthropic,
        model_name="claude-3-7-sonnet",
        is_default=True,
        max_tokens=8192,
        temperature=0.4,
    )

    openai = _build_provider(
        provider_id=2,
        organization_id=12,
        provider_key="openai",
        priority=10,
        api_key="openai-key",
    )
    _build_model(
        model_id=21,
        organization_id=12,
        provider=openai,
        model_name="gpt-4.1-mini",
        is_default=True,
        max_tokens=2048,
        temperature=0.2,
    )

    agent_setting = _build_agent_setting(
        organization_id=12,
        provider_model=anthropic_model,
        sampling_temperature=0.15,
        max_tokens=16384,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=agent_setting))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[openai, anthropic]))

    registry = await provider_service.load_registry(SimpleNamespace(), 12)
    openai_config = registry.get(LLMProvider.OPENAI)
    anthropic_config = registry.get(LLMProvider.ANTHROPIC)

    assert openai_config is not None
    assert openai_config.temperature == pytest.approx(0.2)
    assert openai_config.max_tokens == 2048

    assert anthropic_config is not None
    assert anthropic_config.temperature == pytest.approx(0.15)
    assert anthropic_config.max_tokens == 16384


@pytest.mark.asyncio
async def test_load_registry_skips_unsupported_persisted_provider_keys(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    unsupported = _build_provider(
        provider_id=8,
        organization_id=15,
        provider_key="custom-llm",
        priority=1,
        api_key="custom-key",
    )
    _build_model(
        model_id=81,
        organization_id=15,
        provider=unsupported,
        model_name="custom-model",
        is_default=True,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[unsupported]))

    registry = await provider_service.load_registry(SimpleNamespace(), 15)

    assert registry.get(LLMProvider.OPENAI).available is False
    assert [config.provider for config in registry.get_available()] == [LLMProvider.TEMPLATE]


@pytest.mark.asyncio
async def test_load_registry_applies_routing_policy_preferred_provider_with_fallback(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    groq = _build_provider(
        provider_id=1,
        organization_id=21,
        provider_key="groq",
        priority=5,
        api_key="groq-key",
    )
    _build_model(
        model_id=11,
        organization_id=21,
        provider=groq,
        model_name="llama-4-scout",
        is_default=True,
    )

    openai = _build_provider(
        provider_id=2,
        organization_id=21,
        provider_key="openai",
        priority=50,
        api_key="openai-key",
    )
    openai_model = _build_model(
        model_id=21,
        organization_id=21,
        provider=openai,
        model_name="gpt-4.1-mini",
        is_default=True,
    )
    routing_policy = _build_routing_policy(
        organization_id=21,
        provider=openai,
        provider_model=openai_model,
        fallback_to_priority_order=True,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=routing_policy))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[groq, openai]))

    registry = await provider_service.load_registry(SimpleNamespace(), 21)
    available = registry.get_available()

    assert [config.provider for config in available] == [LLMProvider.OPENAI]
    assert available[0].model == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_load_registry_respects_routing_policy_without_managed_fallback(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    groq = _build_provider(
        provider_id=1,
        organization_id=22,
        provider_key="groq",
        priority=5,
        api_key="groq-key",
    )
    _build_model(
        model_id=11,
        organization_id=22,
        provider=groq,
        model_name="llama-4-scout",
        is_default=True,
    )

    openai = _build_provider(
        provider_id=2,
        organization_id=22,
        provider_key="openai",
        priority=50,
        api_key="",
    )
    openai.is_enabled = True
    openai_model = _build_model(
        model_id=21,
        organization_id=22,
        provider=openai,
        model_name="gpt-4.1-mini",
        is_default=True,
    )
    routing_policy = _build_routing_policy(
        organization_id=22,
        provider=openai,
        provider_model=openai_model,
        fallback_to_priority_order=False,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=routing_policy))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[groq, openai]))

    registry = await provider_service.load_registry(SimpleNamespace(), 22)

    assert registry.get_available() == []


@pytest.mark.asyncio
async def test_load_registry_keeps_ollama_configurable_without_api_key(
    monkeypatch,
    deterministic_registry_defaults,
    provider_service,
):
    ollama = _build_provider(
        provider_id=3,
        organization_id=33,
        provider_key="ollama",
        priority=70,
        api_key="",
        base_url="http://localhost:11434",
    )
    _build_model(
        model_id=31,
        organization_id=33,
        provider=ollama,
        model_name="llama3.2:3b",
        is_default=True,
    )

    monkeypatch.setattr("app.modules.ai.service.set_tenant_context", AsyncMock())
    monkeypatch.setattr(provider_service, "_get_agent_setting", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_routing_policy", AsyncMock(return_value=None))
    monkeypatch.setattr(provider_service, "_get_providers", AsyncMock(return_value=[ollama]))

    registry = await provider_service.load_registry(SimpleNamespace(), 33)
    config = registry.get(LLMProvider.OLLAMA)

    assert config is not None
    assert config.base_url == "http://localhost:11434"
    assert config.model == "llama3.2:3b"
    assert config.source == "local_runtime"
    assert config.available is True