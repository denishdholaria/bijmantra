"""
AI Domain Service Layer

Business logic for Veena AI assistant, RAG, and ML services.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rls import set_tenant_context
from app.models.ai_configuration import AIProvider, AIProviderModel, ReevuAgentSetting, ReevuRoutingPolicy
from app.modules.ai.adapters import ProviderRegistry
from app.modules.ai.services.provider_types import LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class AIProviderService:
	"""Loads org-scoped AI provider configuration for REEVU."""

	DEFAULT_AGENT_KEY = "reevu"

	async def load_registry(
		self,
		db: AsyncSession,
		organization_id: int,
		*,
		agent_key: str = DEFAULT_AGENT_KEY,
		is_superuser: bool = False,
	) -> ProviderRegistry:
		"""Build a ProviderRegistry from persisted org settings with env fallback."""
		await set_tenant_context(db, organization_id, is_superuser)

		registry = ProviderRegistry()
		agent_setting = await self._get_agent_setting(db, organization_id, agent_key)
		routing_policy = await self._get_routing_policy(db, organization_id, agent_key)
		providers = await self._get_providers(db, organization_id)

		if not providers:
			return registry

		for provider_type, config in list(registry.providers.items()):
			if provider_type == LLMProvider.TEMPLATE:
				continue
			config.available = False
			registry.register(provider_type, config)

		for provider in providers:
			provider_type = self._parse_provider_key(provider.provider_key)
			if provider_type is None:
				logger.warning("[Veena] Skipping unsupported persisted provider: %s", provider.provider_key)
				continue

			base_config = registry.get(provider_type)
			selected_model = self._select_provider_model(provider, agent_setting, routing_policy)

			model_name = selected_model.model_name if selected_model else (base_config.model if base_config else None)
			if not model_name:
				logger.warning("[Veena] Skipping provider %s without a model", provider.provider_key)
				continue

			# ADR-004: Use explicit property to signal plaintext semantics
			api_key = provider.api_key_plaintext or (base_config.api_key if base_config else None)
			base_url = provider.base_url or (base_config.base_url if base_config else None)
			max_tokens = self._resolve_max_tokens(base_config, selected_model, agent_setting, provider.id)
			temperature = self._resolve_temperature(base_config, selected_model, agent_setting, provider.id)

			registry.register(
				provider_type,
				LLMConfig(
					provider=provider_type,
					model=model_name,
					source="organization_config" if provider.api_key_plaintext else (base_config.source if base_config else "organization_config"),
					api_key=api_key,
					base_url=base_url,
					max_tokens=max_tokens,
					temperature=temperature,
					available=provider.is_enabled and self._provider_has_runtime_configuration(provider_type, api_key, base_url),
					free_tier=base_config.free_tier if base_config else True,
					rate_limit=base_config.rate_limit if base_config else None,
				),
			)
			registry.configure_priority(provider_type, provider.priority)

		preferred_provider = self._resolve_preferred_provider(agent_setting, routing_policy)
		if preferred_provider is not None:
			registry.set_preferred_provider(preferred_provider)
			registry.set_preferred_provider_only(self._should_lock_preferred_provider(agent_setting, routing_policy))

		return registry

	async def _get_routing_policy(
		self,
		db: AsyncSession,
		organization_id: int,
		agent_key: str,
	) -> ReevuRoutingPolicy | None:
		stmt = (
			select(ReevuRoutingPolicy)
			.options(
				selectinload(ReevuRoutingPolicy.provider),
				selectinload(ReevuRoutingPolicy.provider_model).selectinload(AIProviderModel.provider),
			)
			.where(
				ReevuRoutingPolicy.organization_id == organization_id,
				ReevuRoutingPolicy.agent_key == agent_key,
				ReevuRoutingPolicy.is_active.is_(True),
			)
		)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	async def _get_providers(self, db: AsyncSession, organization_id: int) -> list[AIProvider]:
		stmt = (
			select(AIProvider)
			.options(selectinload(AIProvider.models))
			.where(
				AIProvider.organization_id == organization_id,
				AIProvider.is_enabled.is_(True),
			)
			.order_by(AIProvider.priority.asc(), AIProvider.id.asc())
		)
		result = await db.execute(stmt)
		return list(result.scalars().unique().all())

	async def _get_agent_setting(
		self,
		db: AsyncSession,
		organization_id: int,
		agent_key: str,
	) -> ReevuAgentSetting | None:
		stmt = (
			select(ReevuAgentSetting)
			.options(
				selectinload(ReevuAgentSetting.provider),
				selectinload(ReevuAgentSetting.provider_model).selectinload(AIProviderModel.provider),
			)
			.where(
				ReevuAgentSetting.organization_id == organization_id,
				ReevuAgentSetting.agent_key == agent_key,
				ReevuAgentSetting.is_active.is_(True),
			)
		)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	async def get_agent_setting(
		self,
		db: AsyncSession,
		organization_id: int,
		*,
		agent_key: str = DEFAULT_AGENT_KEY,
		is_superuser: bool = False,
	) -> ReevuAgentSetting | None:
		await set_tenant_context(db, organization_id, is_superuser)
		return await self._get_agent_setting(db, organization_id, agent_key)

	def _parse_provider_key(self, provider_key: str | None) -> LLMProvider | None:
		if not provider_key:
			return None

		try:
			return LLMProvider(provider_key.lower())
		except ValueError:
			return None

	def _resolve_preferred_provider(
		self,
		agent_setting: ReevuAgentSetting | None,
		routing_policy: ReevuRoutingPolicy | None,
	) -> LLMProvider | None:
		if agent_setting is None:
			return self._resolve_policy_preferred_provider(routing_policy)

		if agent_setting.provider is not None:
			return self._parse_provider_key(agent_setting.provider.provider_key)

		if agent_setting.provider_model is not None and agent_setting.provider_model.provider is not None:
			return self._parse_provider_key(agent_setting.provider_model.provider.provider_key)

		return self._resolve_policy_preferred_provider(routing_policy)

	def _resolve_policy_preferred_provider(
		self,
		routing_policy: ReevuRoutingPolicy | None,
	) -> LLMProvider | None:
		if routing_policy is None:
			return None

		if routing_policy.provider is not None:
			return self._parse_provider_key(routing_policy.provider.provider_key)

		if routing_policy.provider_model is not None and routing_policy.provider_model.provider is not None:
			return self._parse_provider_key(routing_policy.provider_model.provider.provider_key)

		return None

	def _select_provider_model(
		self,
		provider: AIProvider,
		agent_setting: ReevuAgentSetting | None,
		routing_policy: ReevuRoutingPolicy | None,
	) -> AIProviderModel | None:
		active_models = [model for model in provider.models if model.is_active]

		if agent_setting and agent_setting.provider_model_id is not None:
			for model in active_models:
				if model.id == agent_setting.provider_model_id:
					return model

		if routing_policy and routing_policy.preferred_provider_model_id is not None:
			for model in active_models:
				if model.id == routing_policy.preferred_provider_model_id:
					return model

		for model in active_models:
			if model.is_default:
				return model

		return active_models[0] if active_models else None

	def _resolve_temperature(
		self,
		base_config: LLMConfig | None,
		provider_model: AIProviderModel | None,
		agent_setting: ReevuAgentSetting | None,
		provider_id: int,
	) -> float:
		if agent_setting and self._agent_targets_provider(agent_setting, provider_id):
			if agent_setting.sampling_temperature is not None:
				return agent_setting.sampling_temperature

		if provider_model and provider_model.temperature is not None:
			return provider_model.temperature

		return base_config.temperature if base_config else 0.7

	def _resolve_max_tokens(
		self,
		base_config: LLMConfig | None,
		provider_model: AIProviderModel | None,
		agent_setting: ReevuAgentSetting | None,
		provider_id: int,
	) -> int:
		if agent_setting and self._agent_targets_provider(agent_setting, provider_id):
			if agent_setting.max_tokens is not None:
				return agent_setting.max_tokens

		if provider_model and provider_model.max_tokens is not None:
			return provider_model.max_tokens

		return base_config.max_tokens if base_config else 1024

	def _agent_targets_provider(
		self,
		agent_setting: ReevuAgentSetting,
		provider_id: int,
	) -> bool:
		return (
			agent_setting.provider_id == provider_id
			or (agent_setting.provider_model is not None and agent_setting.provider_model.provider_id == provider_id)
		)

	def _provider_has_runtime_configuration(
		self,
		provider_type: LLMProvider,
		api_key: str | None,
		base_url: str | None,
	) -> bool:
		if provider_type == LLMProvider.TEMPLATE:
			return True

		if provider_type == LLMProvider.OLLAMA:
			return bool(base_url)

		return bool(api_key)

	def _should_lock_preferred_provider(
		self,
		agent_setting: ReevuAgentSetting | None,
		routing_policy: ReevuRoutingPolicy | None,
	) -> bool:
		if agent_setting is not None and (
			agent_setting.provider_id is not None or agent_setting.provider_model_id is not None
		):
			return False

		return bool(routing_policy and not routing_policy.fallback_to_priority_order)


_ai_provider_service: AIProviderService | None = None


def get_ai_provider_service() -> AIProviderService:
	"""Return the shared AI provider configuration service."""
	global _ai_provider_service
	if _ai_provider_service is None:
		_ai_provider_service = AIProviderService()
	return _ai_provider_service
