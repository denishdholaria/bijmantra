"""Central provider configuration and selection for REEVU."""

from __future__ import annotations

import logging
from math import inf

from app.modules.ai.services.model_catalog import get_default_provider_model
from app.modules.ai.services.provider_types import LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Centralized provider configuration and priority-based selection."""

    PRIORITY_ORDER = [
        LLMProvider.GROQ,
        LLMProvider.GOOGLE,
        LLMProvider.FUNCTIONGEMMA,
        LLMProvider.HUGGINGFACE,
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.OLLAMA,
        LLMProvider.TEMPLATE,
    ]

    def __init__(self) -> None:
        self.providers: dict[LLMProvider, LLMConfig] = {}
        self._preferred_provider: LLMProvider | None = None
        self._preferred_provider_only = False
        self._priority_overrides: dict[LLMProvider, int] = {}
        self._initialize_from_settings()

    def _initialize_from_settings(self) -> None:
        """Load provider configs from backend settings."""
        from app.core.config import settings

        groq_key = settings.GROQ_API_KEY
        self.register(
            LLMProvider.GROQ,
            LLMConfig(
                provider=LLMProvider.GROQ,
                model=settings.GROQ_MODEL,
                source="server_env",
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                available=bool(groq_key),
                free_tier=True,
                rate_limit=30,
            ),
        )

        self.register(
            LLMProvider.OLLAMA,
            LLMConfig(
                provider=LLMProvider.OLLAMA,
                model=settings.OLLAMA_MODEL,
                source="local_runtime",
                base_url=settings.OLLAMA_HOST,
                available=False,
                free_tier=True,
            ),
        )

        google_key = settings.GOOGLE_AI_KEY
        self.register(
            LLMProvider.GOOGLE,
            LLMConfig(
                provider=LLMProvider.GOOGLE,
                model=settings.GOOGLE_MODEL,
                source="server_env",
                api_key=google_key,
                base_url="https://generativelanguage.googleapis.com/v1beta",
                available=bool(google_key),
                free_tier=True,
                rate_limit=60,
            ),
        )

        hf_key = settings.HUGGINGFACE_API_KEY
        self.register(
            LLMProvider.HUGGINGFACE,
            LLMConfig(
                provider=LLMProvider.HUGGINGFACE,
                model=settings.HF_MODEL,
                source="server_env",
                api_key=hf_key,
                base_url="https://api-inference.huggingface.co/models",
                available=bool(hf_key),
                free_tier=True,
                rate_limit=10,
            ),
        )

        functiongemma_key = settings.FUNCTIONGEMMA_API_KEY or hf_key
        self.register(
            LLMProvider.FUNCTIONGEMMA,
            LLMConfig(
                provider=LLMProvider.FUNCTIONGEMMA,
                model=get_default_provider_model("functiongemma", "google/functiongemma-270m-it"),
                source="server_env",
                api_key=functiongemma_key,
                base_url="https://api-inference.huggingface.co/models",
                available=bool(functiongemma_key),
                free_tier=True,
                rate_limit=10,
                max_tokens=512,
                temperature=0.1,
            ),
        )

        openai_key = settings.OPENAI_API_KEY
        self.register(
            LLMProvider.OPENAI,
            LLMConfig(
                provider=LLMProvider.OPENAI,
                model=settings.OPENAI_MODEL,
                source="server_env",
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                available=bool(openai_key),
                free_tier=False,
                rate_limit=60,
            ),
        )

        anthropic_key = settings.ANTHROPIC_API_KEY
        self.register(
            LLMProvider.ANTHROPIC,
            LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model=settings.ANTHROPIC_MODEL,
                source="server_env",
                api_key=anthropic_key,
                base_url="https://api.anthropic.com/v1",
                available=bool(anthropic_key),
                free_tier=False,
                rate_limit=60,
            ),
        )

        self.register(
            LLMProvider.TEMPLATE,
            LLMConfig(
                provider=LLMProvider.TEMPLATE,
                model=get_default_provider_model("template", "template-v1"),
                source="template_builtin",
                available=True,
                free_tier=True,
            ),
        )

    def register(self, provider: LLMProvider, config: LLMConfig) -> None:
        """Register or replace a provider config."""
        self.providers[provider] = config

    def set_preferred_provider(self, provider: LLMProvider | None) -> None:
        """Set an org- or agent-scoped preferred provider."""
        self._preferred_provider = provider

    def set_preferred_provider_only(self, preferred_only: bool) -> None:
        """Control whether managed routing may fall back beyond the preferred provider."""
        self._preferred_provider_only = preferred_only

    def configure_priority(self, provider: LLMProvider, priority: int) -> None:
        """Override canonical ordering with a persisted priority value."""
        self._priority_overrides[provider] = priority

    def get(self, provider: LLMProvider) -> LLMConfig | None:
        """Get a single provider config."""
        return self.providers.get(provider)

    def set_temporary_config(self, provider: LLMProvider, config: LLMConfig) -> None:
        """Temporarily override a provider config, used by BYOK flows."""
        self.providers[provider] = config

    def get_available(self, forced_provider: str | None = None) -> list[LLMConfig]:
        """Return available providers in canonical priority order."""
        provider_name = forced_provider or (self._preferred_provider.value if self._preferred_provider else None)
        if provider_name:
            try:
                provider = LLMProvider(provider_name.lower())
                config = self.providers.get(provider)
                if config and config.available:
                    return [config]
                if forced_provider is not None or self._preferred_provider_only:
                    return []
            except ValueError:
                logger.warning("[REEVU] Unknown forced provider: %s", provider_name)
                if forced_provider is not None:
                    return []

        available: list[LLMConfig] = []
        for provider in self.PRIORITY_ORDER:
            config = self.providers.get(provider)
            if config and config.available:
                available.append(config)

        canonical_index = {
            provider: index
            for index, provider in enumerate(self.PRIORITY_ORDER)
        }
        available.sort(
            key=lambda config: (
                self._priority_overrides.get(config.provider, inf),
                canonical_index.get(config.provider, len(self.PRIORITY_ORDER)),
            )
        )

        return available

    def get_health_status(self) -> dict[str, bool]:
        """Return availability state for each registered provider."""
        return {
            provider.value: config.available
            for provider, config in self.providers.items()
        }

    def get_routing_state(self) -> dict[str, str | bool | None]:
        """Describe the currently configured routing posture."""
        preferred_provider = self._preferred_provider.value if self._preferred_provider else None
        if preferred_provider and self._preferred_provider_only:
            selection_mode = "preferred_only"
        elif preferred_provider:
            selection_mode = "preferred_with_fallback"
        else:
            selection_mode = "priority_order"

        return {
            "preferred_provider": preferred_provider,
            "preferred_provider_only": self._preferred_provider_only,
            "selection_mode": selection_mode,
        }