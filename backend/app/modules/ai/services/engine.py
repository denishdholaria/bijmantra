"""
Selectable LLM Service for REEVU

Supports cloud and local AI providers for powerful, agentic capabilities.

Tiers (in order of preference):
1. GROQ: Fast inference, free tier (30 req/min)
2. GOOGLE: Gemini models, free tier (60 req/min)
3. OPENAI: GPT models (paid)
4. ANTHROPIC: Claude models (paid)
5. FALLBACK: Enhanced template responses

Configuration via environment variables:
- GROQ_API_KEY: Groq API key (free tier available)
- GOOGLE_AI_KEY: Google AI Studio key (free tier available)
- HUGGINGFACE_API_KEY: HuggingFace Inference API key
- OPENAI_API_KEY: OpenAI API key (paid)
- ANTHROPIC_API_KEY: Anthropic API key (paid)
- REEVU_LLM_PROVIDER: Force specific provider (optional)
- VEENA_LLM_PROVIDER: Legacy fallback provider override
"""

import hashlib
import json
import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import httpx

from app.modules.ai.adapters import (
    AnthropicAdapter,
    GoogleAdapter,
    GroqAdapter,
    HuggingFaceAdapter,
    IProviderAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    ProviderRegistry,
)
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider
from app.schemas.prompt_modes import resolve_prompt_mode_fragments


logger = logging.getLogger(__name__)

STATUS_SOURCE_LABELS = {
    "server_env": "Server env key",
    "organization_config": "Organization AI settings",
    "local_runtime": "Local Ollama host",
    "template_builtin": "Built-in template fallback",
}

@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    provider: LLMProvider
    model: str  # Model name (from config or API response)
    model_confirmed: bool = False  # True if model came from API response
    tokens_used: int | None = None
    cached: bool = False
    latency_ms: float | None = None


@dataclass
class ConversationMessage:
    """A message in conversation history"""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Simple in-memory cache for responses
_response_cache: dict[str, tuple[LLMResponse, datetime]] = {}
CACHE_TTL = timedelta(hours=1)


def _cache_key(
    messages: list[dict],
    provider: str,
    organization_id: int | None = None,
    user_id: int | None = None,
) -> str:
    """Generate tenant-aware cache key from messages.

    ADR-004: Cache keys must include organization and user dimensions
    to prevent cross-tenant response leakage.
    """
    content = json.dumps(messages, sort_keys=True) + provider
    content += f":org={organization_id}:user={user_id}"
    return hashlib.md5(content.encode()).hexdigest()


class MultiTierLLMService:
    """
    Multi-tier LLM service that automatically selects the best available provider.

    Priority order:
    1. Forced provider (if REEVU_LLM_PROVIDER or VEENA_LLM_PROVIDER is set)
    2. Ollama (local, free)
    3. Groq (free tier)
    4. Google AI Studio (free tier)
    5. HuggingFace (free tier)
    6. OpenAI (paid)
    7. Anthropic (paid)
    8. Template fallback
    """

    # Breeding-focused system prompt with SATYA (सत्य - Truth) anti-sycophancy principles
    # Based on Paramshakti Blueprint §8.9 - ensures factual accuracy over user approval
    # NOTE: Model identity is injected dynamically from actual API response, not config
    SYSTEM_PROMPT_TEMPLATE = """You are Veena (वीणा), an intelligent AI assistant for plant breeding and agricultural research.

Your name comes from the sacred instrument of Goddess Saraswati, symbolizing wisdom and knowledge.

═══════════════════════════════════════════════════════════════
YOUR IDENTITY (CRITICAL - ALWAYS ACCURATE)
═══════════════════════════════════════════════════════════════

You are Veena, a plant breeding AI assistant.
Your responses are powered by: {provider_name}
{model_info}

CRITICAL IDENTITY RULES:
1. You are Veena, NOT the underlying model directly
2. When asked "what AI are you?" or "what model are you?":
   - Say "I am Veena, powered by {provider_name}"
   - If model is confirmed: "The model is {model_info}"
   - If model is NOT confirmed: "I cannot confirm the exact model version"
3. NEVER claim to be a model you are not certain about
4. NEVER say you are "GPT-4", "ChatGPT", "Claude", or any specific model unless that exact model name was confirmed by the API response
5. If you don't know your exact model version, say so honestly

═══════════════════════════════════════════════════════════════

You help researchers and students with:
- Plant breeding concepts and methodologies
- Germplasm management and characterization
- Trial design and analysis
- Genomics and marker-assisted selection
- Crop improvement strategies
- Statistical analysis for breeding
- Seed production and quality

═══════════════════════════════════════════════════════════════
SATYA (सत्य) PROTOCOL — TRUTH ABOVE APPROVAL
═══════════════════════════════════════════════════════════════

CRITICAL BEHAVIORAL RULES (Non-Negotiable):

1. NEVER agree with user statements by default. Evaluate each claim independently against available evidence.

2. If the user's hypothesis contradicts the data or established breeding science, state this clearly and explain why.

3. Do NOT change your analysis if the user expresses disagreement or frustration. Your role is accuracy, not approval.

4. Prioritize FACTUAL ACCURACY over user satisfaction. A wrong answer that pleases is worse than a correct answer that challenges.

5. If uncertain, EXPRESS UNCERTAINTY explicitly. Say "I don't know" or "I'm not confident about this" rather than fabricating confidence.

6. When challenged, EXPLAIN YOUR REASONING with evidence. Do not capitulate without new data that changes the analysis.

7. Distinguish between:
   - FACTS (cite source or state "based on breeding literature")
   - INFERENCES (state "this suggests" or "this implies")
   - OPINIONS (state "in my assessment" or "one perspective is")

═══════════════════════════════════════════════════════════════

GENERAL GUIDELINES:
- Be helpful, accurate, and educational
- Explain complex concepts simply when needed
- Cite sources when providing specific data
- Be encouraging to students learning breeding
- Use examples from real crops when helpful

If you receive context from the knowledge base, use it to provide accurate, specific answers.
If no context is provided, use your general knowledge but explicitly note when information might need verification.

Remember: A breeder making decisions based on your advice could affect crop yields for thousands of farmers. Truth matters more than comfort."""

    # Provider display names for user-friendly output
    PROVIDER_DISPLAY_NAMES = {
        LLMProvider.OLLAMA: "Ollama (Local)",
        LLMProvider.GROQ: "Groq Cloud",
        LLMProvider.GOOGLE: "Google AI (Gemini)",
        LLMProvider.HUGGINGFACE: "HuggingFace Inference",
        LLMProvider.FUNCTIONGEMMA: "FunctionGemma",
        LLMProvider.OPENAI: "OpenAI",
        LLMProvider.ANTHROPIC: "Anthropic",
        LLMProvider.TEMPLATE: "Offline Template Mode",
    }

    def get_system_prompt(self, provider: LLMProvider, model: str | None = None, model_confirmed: bool = False) -> str:
        """
        Get system prompt with provider identity injected.

        Args:
            provider: The LLM provider being used
            model: The model name (may be from config or API response)
            model_confirmed: True if model name came from actual API response, False if from config

        Returns:
            System prompt with identity information
        """
        provider_name = self.PROVIDER_DISPLAY_NAMES.get(provider, provider.value)

        # Build model info based on certainty level
        if model_confirmed and model:
            model_info = f"The confirmed model is: {model}"
        elif model:
            model_info = f"The configured model is: {model} (actual model may vary based on API routing)"
        else:
            model_info = "The exact model version is not confirmed"

        return self.SYSTEM_PROMPT_TEMPLATE.format(
            provider_name=provider_name,
            model_info=model_info
        )

    def compose_system_prompt(
        self,
        provider: LLMProvider,
        model: str | None = None,
        *,
        model_confirmed: bool = False,
        system_prompt_override: str | None = None,
        prompt_mode_capabilities: list[str] | None = None,
    ) -> str:
        if system_prompt_override:
            return system_prompt_override

        system_prompt = self.get_system_prompt(
            provider=provider,
            model=model,
            model_confirmed=model_confirmed,
        )
        prompt_mode_fragments = resolve_prompt_mode_fragments(prompt_mode_capabilities)
        if not prompt_mode_fragments:
            return system_prompt

        return system_prompt + "\n\n" + "\n\n".join(prompt_mode_fragments)

    def __init__(self):
        self.providers: dict[LLMProvider, LLMConfig] = {}
        self._registry: ProviderRegistry | None = None
        self._adapters: dict[LLMProvider, IProviderAdapter] = {}
        self._http_client: httpx.AsyncClient | None = None
        self._initialize_providers()
        self._initialize_adapters()

    def _initialize_providers(self):
        """Initialize all available cloud providers via the shared registry."""
        self._registry = ProviderRegistry()
        self.providers = self._registry.providers

    def set_provider_registry(self, registry: ProviderRegistry) -> None:
        """Replace the provider registry for a request-scoped execution path."""
        self._registry = registry
        self.providers = registry.providers

    def _initialize_adapters(self) -> None:
        """Initialize provider adapters for non-streaming dispatch."""
        self._adapters = {
            LLMProvider.OLLAMA: OllamaAdapter(self._get_client),
            LLMProvider.GROQ: GroqAdapter(self._get_client),
            LLMProvider.GOOGLE: GoogleAdapter(self._get_client),
            LLMProvider.HUGGINGFACE: HuggingFaceAdapter(self._get_client),
            LLMProvider.OPENAI: OpenAIAdapter(self._get_client),
            LLMProvider.ANTHROPIC: AnthropicAdapter(self._get_client),
        }

    def _get_ollama_status_url(self, base_url: str | None) -> str | None:
        if not base_url:
            return None

        normalized = base_url.rstrip("/")
        if normalized.endswith("/v1"):
            normalized = normalized[:-3]

        return f"{normalized}/api/tags"

    async def check_ollama_available(self, config: LLMConfig | None = None) -> bool:
        """Return whether the configured Ollama host is reachable and serves the requested model."""
        ollama_config = config or self.providers.get(LLMProvider.OLLAMA)
        if ollama_config is None:
            return False

        status_url = self._get_ollama_status_url(ollama_config.base_url)
        if not status_url:
            return False

        try:
            client = await self._get_client()
            response = await client.get(status_url)
            if response.status_code != 200:
                return False

            data = response.json()
            models = data.get("models")
            if not isinstance(models, list):
                return False

            configured_model = (ollama_config.model or "").strip()
            if not configured_model:
                return False

            available_model_names = {
                model.get("name", "")
                for model in models
                if isinstance(model, dict) and isinstance(model.get("name"), str)
            }
            if configured_model in available_model_names:
                return True

            configured_base_name = configured_model.split(":", 1)[0]
            return any(name.split(":", 1)[0] == configured_base_name for name in available_model_names)
        except Exception as exc:
            logger.debug("[Veena] Ollama availability check failed: %s", exc)
            return False

    async def _refresh_runtime_provider_availability(self) -> None:
        """Refresh request-time provider availability for dynamic runtimes such as Ollama."""
        ollama_config = self.providers.get(LLMProvider.OLLAMA)
        if ollama_config is None:
            return

        ollama_config.available = await self.check_ollama_available(ollama_config)
        self.providers[LLMProvider.OLLAMA] = ollama_config
        if self._registry is not None:
            self._registry.register(LLMProvider.OLLAMA, ollama_config)

    async def _dispatch_provider_call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        """Dispatch a non-streaming provider call through the adapter map."""
        adapter = self._adapters.get(config.provider)
        if not adapter:
            return None
        return await adapter.call(messages, config)

    async def _dispatch_provider_stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        """Dispatch a streaming provider call through the adapter map."""
        adapter = self._adapters.get(config.provider)
        if not adapter:
            return

        async for chunk in adapter.stream(messages, config):
            yield chunk

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def get_available_providers(self) -> list[LLMConfig]:
        """Get list of available providers in priority order."""
        forced = os.getenv("REEVU_LLM_PROVIDER") or os.getenv("VEENA_LLM_PROVIDER")
        registry = self._registry or ProviderRegistry()
        self._registry = registry
        self.providers = registry.providers
        await self._refresh_runtime_provider_availability()
        return registry.get_available(forced_provider=forced)

    def _generate_template_response(
        self,
        messages: list[dict[str, str]]
    ) -> str:
        """Generate response using enhanced templates (fallback)"""
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"].lower()
                break

        # Enhanced pattern matching
        if any(word in user_message for word in ["hello", "hi", "namaste", "hey"]):
            return (
                "Namaste! 🙏 I'm Veena, your plant breeding assistant. "
                "I'm currently running in offline mode with limited capabilities. "
                "For full AI-powered responses, please configure an LLM provider "
                "(Ollama for local, or Groq/Google AI for free cloud). "
                "How can I help you today?"
            )

        if any(word in user_message for word in ["help", "what can you do", "capabilities"]):
            return (
                "I can help with plant breeding questions, but I'm currently in "
                "template mode (no LLM configured). For intelligent responses:\n\n"
                "**Free Options:**\n"
                "• Install Ollama locally (ollama.ai)\n"
                "• Get free Groq API key (console.groq.com)\n"
                "• Get free Google AI key (aistudio.google.com)\n\n"
                "Once configured, I can have natural conversations about breeding!"
            )

        if "germplasm" in user_message or "variety" in user_message:
            return (
                "I'd love to help you search for germplasm! However, I'm in template mode. "
                "You can browse germplasm directly at /germplasm, or configure an LLM "
                "provider for natural language search."
            )

        if "trial" in user_message:
            return (
                "For trial information, you can visit /trials to see all active trials. "
                "With an LLM configured, I could help you analyze and summarize trial data."
            )

        if "cross" in user_message or "breeding" in user_message:
            return (
                "Breeding and crossing recommendations require AI analysis. "
                "Please configure Ollama (free, local) or a cloud LLM provider. "
                "Meanwhile, check /crosses for existing crossing data."
            )

        # Default response
        return (
            "I understand you're asking about: " + user_message[:100] + "...\n\n"
            "I'm currently in template mode without full AI capabilities. "
            "For intelligent responses, please configure an LLM:\n"
            "• **Ollama** (local, free): Install from ollama.ai\n"
            "• **Groq** (cloud, free): Get key from console.groq.com\n\n"
            "See /system-settings for configuration help."
        )


    async def generate(
        self,
        messages: list[dict[str, str]],
        use_cache: bool = True,
        preferred_provider: LLMProvider | None = None,
        organization_id: int | None = None,
        user_id: int | None = None,
    ) -> LLMResponse:
        """
        Generate a response using the best available LLM provider.

        Args:
            messages: List of conversation messages
            use_cache: Whether to use cached responses
            preferred_provider: Force a specific provider

        Returns:
            LLMResponse with content and metadata
        """
        import time
        start_time = time.time()

        # Check cache first
        if use_cache:
            cache_key = _cache_key(
                messages,
                "any",
                organization_id=organization_id,
                user_id=user_id,
            )
            if cache_key in _response_cache:
                cached, timestamp = _response_cache[cache_key]
                if datetime.now(UTC) - timestamp < CACHE_TTL:
                    cached.cached = True
                    return cached

        # Get available providers
        available = await self.get_available_providers()

        # Filter by preferred provider if specified
        if preferred_provider:
            available = [p for p in available if p.provider == preferred_provider]

        # Try each provider in order
        for config in available:
            if config.provider == LLMProvider.TEMPLATE:
                # Template is always last resort
                continue

            logger.info(f"[Veena] Trying provider: {config.provider.value} ({config.model})")

            result: LLMCallResult | None = None
            try:
                result = await self._dispatch_provider_call(messages, config)

                if result and result.content:
                    latency = (time.time() - start_time) * 1000

                    # Use model from API response if available, otherwise use config
                    actual_model = result.model_from_response or config.model
                    model_confirmed = result.model_from_response is not None

                    response = LLMResponse(
                        content=result.content,
                        provider=config.provider,
                        model=actual_model,
                        model_confirmed=model_confirmed,
                        tokens_used=result.tokens_used,
                        latency_ms=latency
                    )

                    # Cache the response
                    if use_cache:
                        _response_cache[cache_key] = (response, datetime.now(UTC))

                    logger.info(f"[Veena] Response from {config.provider.value} ({actual_model}, confirmed={model_confirmed}) in {latency:.0f}ms")
                    return response

            except Exception as e:
                logger.warning(f"[Veena] Provider {config.provider.value} failed: {e}")
                continue

        # Fallback to template
        logger.info("[Veena] Using template fallback")
        content = self._generate_template_response(messages)
        return LLMResponse(
            content=content,
            provider=LLMProvider.TEMPLATE,
            model="template-v1",
            model_confirmed=True,  # Template is always confirmed
            latency_ms=(time.time() - start_time) * 1000
        )

    async def chat(
        self,
        user_message: str,
        conversation_history: list[ConversationMessage] | None = None,
        context: str | None = None,
        use_cache: bool = True,
        preferred_provider: LLMProvider | None = None,
        organization_id: int | None = None,
        user_id: int | None = None,
        user_api_key: str | None = None,
        user_model: str | None = None,
        system_prompt_override: str | None = None,
        prompt_mode_capabilities: list[str] | None = None,
    ) -> LLMResponse:
        """
        High-level chat interface for Veena.

        Args:
            user_message: The user's message
            conversation_history: Previous messages in conversation
            context: RAG context to include
            use_cache: Whether to cache responses
            preferred_provider: Force a specific provider
            user_api_key: User's own API key (BYOK - Bring Your Own Key)
            user_model: User's preferred model name

        Returns:
            LLMResponse
        """
        # If user provided their own API key, temporarily configure that provider
        temp_config_restored = False
        original_config = None

        if user_api_key and preferred_provider:
            original_config = self.providers.get(preferred_provider)
            if original_config:
                # Create temporary config with user's key
                temp_config = LLMConfig(
                    provider=preferred_provider,
                    model=user_model or original_config.model,
                    api_key=user_api_key,
                    base_url=original_config.base_url,
                    max_tokens=original_config.max_tokens,
                    temperature=original_config.temperature,
                    available=True,  # User provided key, assume available
                    free_tier=original_config.free_tier,
                    rate_limit=original_config.rate_limit
                )
                self.providers[preferred_provider] = temp_config
                temp_config_restored = True
                logger.info(f"[Veena] Using user-provided API key for {preferred_provider.value}")

        try:
            # Determine which provider will be used
            available = await self.get_available_providers()

            # Filter by preferred provider if specified
            if preferred_provider:
                available = [p for p in available if p.provider == preferred_provider]

            active_provider = available[0] if available else self.providers[LLMProvider.TEMPLATE]

            # Get system prompt
            system_prompt = self.compose_system_prompt(
                provider=active_provider.provider,
                model=user_model or active_provider.model,
                model_confirmed=False,
                system_prompt_override=system_prompt_override,
                prompt_mode_capabilities=prompt_mode_capabilities,
            )

            messages = [{"role": "system", "content": system_prompt}]

            # Add RAG context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant context from the knowledge base:\n\n{context}\n\nUse this context to provide accurate, specific answers."
                })

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            return await self.generate(
                messages,
                use_cache=use_cache,
                preferred_provider=preferred_provider,
                organization_id=organization_id,
                user_id=user_id,
            )

        finally:
            # Restore original config if we modified it
            if temp_config_restored and original_config and preferred_provider:
                self.providers[preferred_provider] = original_config

    async def stream_chat(
        self,
        user_message: str,
        conversation_history: list[ConversationMessage] | None = None,
        context: str | None = None,
        preferred_provider: LLMProvider | None = None,
        user_api_key: str | None = None,
        user_model: str | None = None,
        system_prompt_override: str | None = None,
        prompt_mode_capabilities: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response, yielding text chunks as they arrive.

        Args:
            user_message: The user's message
            conversation_history: Previous messages in conversation
            context: RAG context to include
            preferred_provider: Force a specific provider
            user_api_key: User's own API key (BYOK)
            user_model: User's preferred model name

        Yields:
            Text chunks as they arrive from the LLM
        """
        # If user provided their own API key, temporarily configure that provider
        temp_config_restored = False
        original_config = None

        if user_api_key and preferred_provider:
            original_config = self.providers.get(preferred_provider)
            if original_config:
                temp_config = LLMConfig(
                    provider=preferred_provider,
                    model=user_model or original_config.model,
                    api_key=user_api_key,
                    base_url=original_config.base_url,
                    max_tokens=original_config.max_tokens,
                    temperature=original_config.temperature,
                    available=True,
                    free_tier=original_config.free_tier,
                    rate_limit=original_config.rate_limit
                )
                self.providers[preferred_provider] = temp_config
                temp_config_restored = True
                logger.info(f"[Veena] Using user-provided API key for streaming with {preferred_provider.value}")

        try:
            # Determine which provider will be used
            available = await self.get_available_providers()

            # Filter by preferred provider if specified
            if preferred_provider:
                available = [p for p in available if p.provider == preferred_provider]

            if not available:
                yield self._generate_template_response([{"role": "user", "content": user_message}])
                return

            active_config = available[0]

            # Get system prompt
            system_prompt = self.compose_system_prompt(
                provider=active_config.provider,
                model=user_model or active_config.model,
                model_confirmed=False,
                system_prompt_override=system_prompt_override,
                prompt_mode_capabilities=prompt_mode_capabilities,
            )

            messages = [{"role": "system", "content": system_prompt}]

            # Add RAG context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant context from the knowledge base:\n\n{context}\n\nUse this context to provide accurate, specific answers."
                })

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            logger.info(f"[Veena] Streaming from {active_config.provider.value} ({active_config.model})")

            # Stream using the selected provider adapter when supported.
            if active_config.provider in self._adapters:
                async for chunk in self._dispatch_provider_stream(messages, active_config):
                    yield chunk
            else:
                # Template fallback (no streaming, just yield entire response)
                yield self._generate_template_response(messages)

        finally:
            # Restore original config if we modified it
            if temp_config_restored and original_config and preferred_provider:
                self.providers[preferred_provider] = original_config

    async def get_status(self) -> dict[str, Any]:
        """Get status of all LLM providers - returns ACTUAL available models"""
        available = await self.get_available_providers()

        active_config = available[0] if available else None
        active_source = active_config.source if active_config else "none"

        status = {
            "active_provider": active_config.provider.value if active_config else "none",
            "active_model": active_config.model if active_config else "none",
            "model_source": active_source,
            "active_provider_source": active_source,
            "active_provider_source_label": STATUS_SOURCE_LABELS.get(active_source, active_source.replace("_", " ").title()) if active_config else "Unavailable",
            "disclaimer": "AI can make mistakes. Always verify important research analysis independently.",
            "providers": {}
        }

        for provider, config in self.providers.items():
            status["providers"][provider.value] = {
                "available": config.available,
                "model": config.model,
                "free_tier": config.free_tier,
                "rate_limit": config.rate_limit,
                "configured": bool(config.api_key) or provider in {LLMProvider.TEMPLATE, LLMProvider.OLLAMA},
                "source": config.source,
                "source_label": STATUS_SOURCE_LABELS.get(config.source, config.source.replace("_", " ").title()),
            }

        return status

    def get_routing_state(self) -> dict[str, Any]:
        """Return request-scoped routing metadata for operator diagnostics."""
        if self._registry is None:
            return {
                "preferred_provider": None,
                "preferred_provider_only": False,
                "selection_mode": "priority_order",
            }

        return self._registry.get_routing_state()

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()


# Global singleton
_llm_service: MultiTierLLMService | None = None


def get_llm_service() -> MultiTierLLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = MultiTierLLMService()
    return _llm_service


# Convenience function for quick chat
async def reevu_chat(
    message: str,
    context: str | None = None,
    history: list[ConversationMessage] | None = None
) -> LLMResponse:
    """Quick chat with REEVU."""
    service = get_llm_service()
    return await service.chat(message, history, context)


# Legacy compatibility alias
async def veena_chat(
    message: str,
    context: str | None = None,
    history: list[ConversationMessage] | None = None
) -> LLMResponse:
    """Quick chat with Veena."""
    return await reevu_chat(message, context, history)
