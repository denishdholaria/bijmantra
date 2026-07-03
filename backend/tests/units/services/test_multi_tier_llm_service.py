from unittest.mock import AsyncMock, Mock

import pytest

from app.modules.ai.services.engine import MultiTierLLMService
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


@pytest.mark.asyncio
async def test_check_ollama_available_requires_configured_model_present(monkeypatch):
	service = MultiTierLLMService()
	response = Mock()
	response.status_code = 200
	response.json.return_value = {
		"models": [
			{"name": "llama3.2:3b"},
			{"name": "qwen2.5:3b"},
		],
	}
	client = AsyncMock()
	client.get.return_value = response
	monkeypatch.setattr(service, "_get_client", AsyncMock(return_value=client))

	assert await service.check_ollama_available(
		LLMConfig(
			provider=LLMProvider.OLLAMA,
			model="llama3.2:3b",
			base_url="http://localhost:11434",
		)
	) is True

	assert await service.check_ollama_available(
		LLMConfig(
			provider=LLMProvider.OLLAMA,
			model="mistral:7b",
			base_url="http://localhost:11434",
		)
	) is False


@pytest.mark.asyncio
async def test_get_available_providers_keeps_cloud_default_when_ollama_is_also_reachable(monkeypatch):
	service = MultiTierLLMService()
	service.providers[LLMProvider.GROQ].available = True
	service.providers[LLMProvider.OLLAMA].model = "llama3.2:3b"
	service.providers[LLMProvider.OLLAMA].base_url = "http://localhost:11434"
	monkeypatch.setattr(service, "check_ollama_available", AsyncMock(return_value=True))

	available = await service.get_available_providers()

	assert available[0].provider != LLMProvider.OLLAMA
	assert LLMProvider.OLLAMA in [config.provider for config in available]


@pytest.mark.asyncio
async def test_generate_cache_is_scoped_by_organization_and_user(monkeypatch):
	service = MultiTierLLMService()
	config = LLMConfig(
		provider=LLMProvider.GROQ,
		model="llama-4-scout",
		available=True,
	)
	service.providers = {LLMProvider.GROQ: config, LLMProvider.TEMPLATE: service.providers[LLMProvider.TEMPLATE]}
	monkeypatch.setattr(service, "get_available_providers", AsyncMock(return_value=[config]))

	dispatch = AsyncMock(
		side_effect=[
			LLMCallResult(content="org-1-user-1"),
			LLMCallResult(content="org-2-user-1"),
		]
	)
	monkeypatch.setattr(service, "_dispatch_provider_call", dispatch)

	messages = [{"role": "user", "content": "Same prompt"}]

	first = await service.generate(messages, organization_id=1, user_id=1)
	second = await service.generate(messages, organization_id=2, user_id=1)
	third = await service.generate(messages, organization_id=1, user_id=1)

	assert first.content == "org-1-user-1"
	assert second.content == "org-2-user-1"
	assert third.content == "org-1-user-1"
	assert third.cached is True
	assert dispatch.await_count == 2