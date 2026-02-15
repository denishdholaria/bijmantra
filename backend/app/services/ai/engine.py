"""
Cloud-Based LLM Service for Veena AI

Supports cloud AI providers for powerful, agentic capabilities.

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
- VEENA_LLM_PROVIDER: Force specific provider (optional)
"""

import os
import json
import asyncio
import hashlib
from typing import Optional, List, Dict, Any, Literal, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from enum import Enum
import logging
import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers (Cloud-Only)"""
    GROQ = "groq"               # Free tier: 30 req/min
    GOOGLE = "google"           # Free tier: 60 req/min  
    HUGGINGFACE = "huggingface" # Free tier available
    FUNCTIONGEMMA = "functiongemma"  # Function calling (270M)
    OPENAI = "openai"           # Paid
    ANTHROPIC = "anthropic"     # Paid
    TEMPLATE = "template"       # Fallback, no LLM


@dataclass
class LLMConfig:
    """Configuration for an LLM provider"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    available: bool = False
    free_tier: bool = True
    rate_limit: Optional[int] = None  # requests per minute


@dataclass
class LLMCallResult:
    """Result from a single LLM API call (internal use)"""
    content: str
    model_from_response: Optional[str] = None  # Actual model returned by API
    tokens_used: Optional[int] = None


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    provider: LLMProvider
    model: str  # Model name (from config or API response)
    model_confirmed: bool = False  # True if model came from API response
    tokens_used: Optional[int] = None
    cached: bool = False
    latency_ms: Optional[float] = None


@dataclass
class ConversationMessage:
    """A message in conversation history"""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Simple in-memory cache for responses
_response_cache: Dict[str, tuple[LLMResponse, datetime]] = {}
CACHE_TTL = timedelta(hours=1)


def _cache_key(messages: List[Dict], provider: str) -> str:
    """Generate cache key from messages"""
    content = json.dumps(messages, sort_keys=True) + provider
    return hashlib.md5(content.encode()).hexdigest()


class MultiTierLLMService:
    """
    Multi-tier LLM service that automatically selects the best available provider.
    
    Priority order:
    1. Forced provider (if VEENA_LLM_PROVIDER is set)
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
        LLMProvider.GROQ: "Groq Cloud",
        LLMProvider.GOOGLE: "Google AI (Gemini)",
        LLMProvider.HUGGINGFACE: "HuggingFace Inference",
        LLMProvider.FUNCTIONGEMMA: "FunctionGemma",
        LLMProvider.OPENAI: "OpenAI",
        LLMProvider.ANTHROPIC: "Anthropic",
        LLMProvider.TEMPLATE: "Offline Template Mode",
    }

    def get_system_prompt(self, provider: LLMProvider, model: Optional[str] = None, model_confirmed: bool = False) -> str:
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

    def __init__(self):
        self.providers: Dict[LLMProvider, LLMConfig] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available cloud providers"""
        from app.core.config import settings
        
        # 1. Groq (Free tier: 30 req/min)
        groq_key = settings.GROQ_API_KEY
        self.providers[LLMProvider.GROQ] = LLMConfig(
            provider=LLMProvider.GROQ,
            model=settings.GROQ_MODEL,
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            available=bool(groq_key),
            free_tier=True,
            rate_limit=30
        )
        
        # 3. Google AI Studio (Free tier: 60 req/min)
        # Model names evolve rapidly - use "latest" suffix when available
        # Reference: https://ai.google.dev/gemini-api/docs/models/gemini
        google_key = settings.GOOGLE_AI_KEY
        self.providers[LLMProvider.GOOGLE] = LLMConfig(
            provider=LLMProvider.GOOGLE,
            model=settings.GOOGLE_MODEL,
            api_key=google_key,
            base_url="https://generativelanguage.googleapis.com/v1beta",
            available=bool(google_key),
            free_tier=True,
            rate_limit=60
        )
        
        # 4. HuggingFace (Free tier)
        hf_key = settings.HUGGINGFACE_API_KEY
        self.providers[LLMProvider.HUGGINGFACE] = LLMConfig(
            provider=LLMProvider.HUGGINGFACE,
            model=settings.HF_MODEL,
            api_key=hf_key,
            base_url="https://api-inference.huggingface.co/models",
            available=bool(hf_key),
            free_tier=True,
            rate_limit=10
        )
        
        # 5. FunctionGemma (Function calling, 270M)
        # Can use same HuggingFace key or separate
        functiongemma_key = settings.FUNCTIONGEMMA_API_KEY or hf_key
        self.providers[LLMProvider.FUNCTIONGEMMA] = LLMConfig(
            provider=LLMProvider.FUNCTIONGEMMA,
            model="google/functiongemma-270m-it",
            api_key=functiongemma_key,
            base_url="https://api-inference.huggingface.co/models",
            available=bool(functiongemma_key),
            free_tier=True,
            rate_limit=10,
            max_tokens=512,  # Smaller for function calling
            temperature=0.1  # Lower temp for structured output
        )
        
        # 6. OpenAI (Paid)
        openai_key = settings.OPENAI_API_KEY
        self.providers[LLMProvider.OPENAI] = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=settings.OPENAI_MODEL,
            api_key=openai_key,
            base_url="https://api.openai.com/v1",
            available=bool(openai_key),
            free_tier=False,
            rate_limit=60
        )
        
        # 7. Anthropic (Paid)
        anthropic_key = settings.ANTHROPIC_API_KEY
        self.providers[LLMProvider.ANTHROPIC] = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model=settings.ANTHROPIC_MODEL,
            api_key=anthropic_key,
            base_url="https://api.anthropic.com/v1",
            available=bool(anthropic_key),
            free_tier=False,
            rate_limit=60
        )
        
        # 8. Template fallback (always available)
        self.providers[LLMProvider.TEMPLATE] = LLMConfig(
            provider=LLMProvider.TEMPLATE,
            model="template-v1",
            available=True,
            free_tier=True
        )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def get_available_providers(self) -> List[LLMConfig]:
        """Get list of available cloud providers in priority order\""""
        
        # Check forced provider
        forced = os.getenv("VEENA_LLM_PROVIDER")
        if forced:
            try:
                provider = LLMProvider(forced.lower())
                config = self.providers.get(provider)
                if config and config.available:
                    return [config]
            except ValueError:
                logger.warning(f"[Veena] Unknown forced provider: {forced}")
        
        # Return available providers in priority order (Cloud-Only)
        priority_order = [
            LLMProvider.GROQ,        # Fast free cloud
            LLMProvider.GOOGLE,      # Good free tier
            LLMProvider.FUNCTIONGEMMA, # Function calling
            LLMProvider.HUGGINGFACE, # Free but slower
            LLMProvider.OPENAI,      # Paid
            LLMProvider.ANTHROPIC,   # Paid
            LLMProvider.TEMPLATE,    # Always available
        ]
        
        available = []
        for provider in priority_order:
            config = self.providers.get(provider)
            if config and config.available:
                available.append(config)
        
        return available


    async def _call_groq(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[LLMCallResult]:
        """Call Groq API (OpenAI-compatible) - returns actual model from response"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # OpenAI-compatible APIs return model in response
                model_from_response = data.get("model")
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                content = data["choices"][0]["message"]["content"].strip()
                
                return LLMCallResult(
                    content=content,
                    model_from_response=model_from_response,
                    tokens_used=tokens_used
                )
        except Exception as e:
            logger.error(f"[Veena] Groq error: {e}")
        return None
    
    async def _call_google(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[LLMCallResult]:
        """Call Google AI Studio API - returns actual model from response"""
        try:
            client = await self._get_client()
            
            # Convert to Google format
            contents = []
            system_instruction = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
            
            body = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": config.max_tokens,
                    "temperature": config.temperature,
                }
            }
            
            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
            response = await client.post(
                f"{config.base_url}/models/{config.model}:generateContent?key={config.api_key}",
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract actual model from response metadata
                model_from_response = data.get("modelVersion") or data.get("model")
                
                # Extract token usage if available
                usage = data.get("usageMetadata", {})
                tokens_used = usage.get("totalTokenCount")
                
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "").strip()
                        return LLMCallResult(
                            content=content,
                            model_from_response=model_from_response,
                            tokens_used=tokens_used
                        )
        except Exception as e:
            logger.error(f"[Veena] Google AI error: {e}")
        return None
    
    async def _call_huggingface(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[LLMCallResult]:
        """Call HuggingFace Inference API"""
        try:
            client = await self._get_client()
            
            # Format as conversation
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"<|system|>\n{msg['content']}</s>\n"
                elif msg["role"] == "user":
                    prompt += f"<|user|>\n{msg['content']}</s>\n"
                elif msg["role"] == "assistant":
                    prompt += f"<|assistant|>\n{msg['content']}</s>\n"
            prompt += "<|assistant|>\n"
            
            response = await client.post(
                f"{config.base_url}/{config.model}",
                headers={"Authorization": f"Bearer {config.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": config.max_tokens,
                        "temperature": config.temperature,
                        "return_full_text": False,
                    }
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    content = data[0].get("generated_text", "").strip()
                    # HuggingFace doesn't return model in response, use config
                    return LLMCallResult(
                        content=content,
                        model_from_response=None,  # Not available from HF API
                        tokens_used=None
                    )
        except Exception as e:
            logger.error(f"[Veena] HuggingFace error: {e}")
        return None
    
    async def _call_openai(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[LLMCallResult]:
        """Call OpenAI API - returns actual model from response"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # OpenAI returns actual model in response
                model_from_response = data.get("model")
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                content = data["choices"][0]["message"]["content"].strip()
                
                return LLMCallResult(
                    content=content,
                    model_from_response=model_from_response,
                    tokens_used=tokens_used
                )
        except Exception as e:
            logger.error(f"[Veena] OpenAI error: {e}")
        return None
    
    async def _call_anthropic(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[LLMCallResult]:
        """Call Anthropic API - returns actual model from response"""
        try:
            client = await self._get_client()
            
            # Extract system message
            system = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    chat_messages.append(msg)
            
            body = {
                "model": config.model,
                "max_tokens": config.max_tokens,
                "messages": chat_messages,
            }
            if system:
                body["system"] = system
            
            response = await client.post(
                f"{config.base_url}/messages",
                headers={
                    "x-api-key": config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                # Anthropic returns actual model in response
                model_from_response = data.get("model")
                usage = data.get("usage", {})
                tokens_used = (usage.get("input_tokens", 0) or 0) + (usage.get("output_tokens", 0) or 0)
                
                content_list = data.get("content", [])
                if content_list:
                    content = content_list[0].get("text", "").strip()
                    return LLMCallResult(
                        content=content,
                        model_from_response=model_from_response,
                        tokens_used=tokens_used if tokens_used else None
                    )
        except Exception as e:
            logger.error(f"[Veena] Anthropic error: {e}")
        return None
    
    def _generate_template_response(
        self, 
        messages: List[Dict[str, str]]
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
        messages: List[Dict[str, str]],
        use_cache: bool = True,
        preferred_provider: Optional[LLMProvider] = None
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
            cache_key = _cache_key(messages, "any")
            if cache_key in _response_cache:
                cached, timestamp = _response_cache[cache_key]
                if datetime.now(UTC) - timestamp < CACHE_TTL:
                    cached.cached = True
                    return cached
        
        # Get available providers
        available = await self.get_available_providers()
        
        # Filter by preferred provider if specified
        if preferred_provider:
            available = [p for p in available if p.provider == preferred_provider] or available
        
        # Try each provider in order
        for config in available:
            if config.provider == LLMProvider.TEMPLATE:
                # Template is always last resort
                continue
            
            logger.info(f"[Veena] Trying provider: {config.provider.value} ({config.model})")
            
            result: Optional[LLMCallResult] = None
            try:
                if config.provider == LLMProvider.GROQ:
                    result = await self._call_groq(messages, config)
                elif config.provider == LLMProvider.GOOGLE:
                    result = await self._call_google(messages, config)
                elif config.provider == LLMProvider.HUGGINGFACE:
                    result = await self._call_huggingface(messages, config)
                elif config.provider == LLMProvider.OPENAI:
                    result = await self._call_openai(messages, config)
                elif config.provider == LLMProvider.ANTHROPIC:
                    result = await self._call_anthropic(messages, config)
                
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
        conversation_history: Optional[List[ConversationMessage]] = None,
        context: Optional[str] = None,
        use_cache: bool = True,
        preferred_provider: Optional[LLMProvider] = None,
        user_api_key: Optional[str] = None,
        user_model: Optional[str] = None
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
                preferred_list = [p for p in available if p.provider == preferred_provider]
                if preferred_list:
                    available = preferred_list
            
            active_provider = available[0] if available else self.providers[LLMProvider.TEMPLATE]
            
            # Get system prompt
            system_prompt = self.get_system_prompt(
                provider=active_provider.provider, 
                model=user_model or active_provider.model,
                model_confirmed=False  # Config value, not from API response
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
            
            return await self.generate(messages, use_cache=use_cache, preferred_provider=preferred_provider)
        
        finally:
            # Restore original config if we modified it
            if temp_config_restored and original_config and preferred_provider:
                self.providers[preferred_provider] = original_config
    
    async def stream_chat(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        context: Optional[str] = None,
        preferred_provider: Optional[LLMProvider] = None,
        user_api_key: Optional[str] = None,
        user_model: Optional[str] = None
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
                preferred_list = [p for p in available if p.provider == preferred_provider]
                if preferred_list:
                    available = preferred_list
            
            if not available:
                yield self._generate_template_response([{"role": "user", "content": user_message}])
                return
            
            active_config = available[0]
            
            # Get system prompt
            system_prompt = self.get_system_prompt(
                provider=active_config.provider, 
                model=user_model or active_config.model,
                model_confirmed=False
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
            
            # Stream based on provider (Cloud-Only)
            if active_config.provider == LLMProvider.GROQ:
                async for chunk in self._stream_groq(messages, active_config):
                    yield chunk
            elif active_config.provider == LLMProvider.GOOGLE:
                async for chunk in self._stream_google(messages, active_config):
                    yield chunk
            elif active_config.provider == LLMProvider.OPENAI:
                async for chunk in self._stream_openai(messages, active_config):
                    yield chunk
            elif active_config.provider == LLMProvider.ANTHROPIC:
                async for chunk in self._stream_anthropic(messages, active_config):
                    yield chunk
            else:
                # Template fallback (no streaming, just yield entire response)
                yield self._generate_template_response(messages)
        
        finally:
            # Restore original config if we modified it
            if temp_config_restored and original_config and preferred_provider:
                self.providers[preferred_provider] = original_config

    async def _stream_groq(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream from Groq API (OpenAI-compatible)"""
        try:
            client = await self._get_client()
            async with client.stream(
                "POST",
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "stream": True,
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"[Veena] Groq streaming error: {e}")
            yield f"[Error: {str(e)}]"

    async def _stream_google(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream from Google AI Studio API"""
        try:
            client = await self._get_client()
            
            # Convert to Google format
            contents = []
            system_instruction = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
            
            body = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": config.max_tokens,
                    "temperature": config.temperature,
                }
            }
            
            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
            async with client.stream(
                "POST",
                f"{config.base_url}/models/{config.model}:streamGenerateContent?alt=sse&key={config.api_key}",
                json=body
            ) as response:
                # Check for HTTP errors first
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"[Veena] Google API error {response.status_code}: {error_text}")
                    yield f"[API Error: {response.status_code}]"
                    return
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            # SSE format: "data: {json}"
                            line = line.strip()
                            if line.startswith('data: '):
                                line = line[6:]  # Remove "data: " prefix
                            
                            if not line:
                                continue
                                
                            data = json.loads(line)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    text = parts[0].get("text", "")
                                    if text:
                                        yield text
                            
                            # Check for errors in response
                            if "error" in data:
                                error_msg = data["error"].get("message", "Unknown error")
                                logger.error(f"[Veena] Google API returned error: {error_msg}")
                                yield f"[Error: {error_msg}]"
                                return
                                
                        except json.JSONDecodeError as e:
                            logger.debug(f"[Veena] Skipping non-JSON line: {line[:100]}")
                            continue
        except Exception as e:
            logger.error(f"[Veena] Google streaming error: {e}")
            yield f"[Error: {str(e)}]"

    async def _stream_openai(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream from OpenAI API"""
        try:
            client = await self._get_client()
            async with client.stream(
                "POST",
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "stream": True,
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"[Veena] OpenAI streaming error: {e}")
            yield f"[Error: {str(e)}]"

    async def _stream_anthropic(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream from Anthropic API"""
        try:
            client = await self._get_client()
            
            # Extract system message
            system = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    chat_messages.append(msg)
            
            body = {
                "model": config.model,
                "max_tokens": config.max_tokens,
                "messages": chat_messages,
                "stream": True,
            }
            if system:
                body["system"] = system
            
            async with client.stream(
                "POST",
                f"{config.base_url}/messages",
                headers={
                    "x-api-key": config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=body
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if "text" in delta:
                                    yield delta["text"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"[Veena] Anthropic streaming error: {e}")
            yield f"[Error: {str(e)}]"
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers - returns ACTUAL available models"""
        available = await self.get_available_providers()
        
        active_config = available[0] if available else None
        
        status = {
            "active_provider": active_config.provider.value if active_config else "none",
            "active_model": active_config.model if active_config else "none",
            "model_source": "configured",  # Cloud models are always from config
            "disclaimer": "AI can make mistakes. Always verify important research analysis independently.",
            "providers": {}
        }
        
        for provider, config in self.providers.items():
            status["providers"][provider.value] = {
                "available": config.available,
                "model": config.model,
                "free_tier": config.free_tier,
                "rate_limit": config.rate_limit,
                "configured": bool(config.api_key) or provider == LLMProvider.TEMPLATE
            }
        
        return status
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()


# Global singleton
_llm_service: Optional[MultiTierLLMService] = None


def get_llm_service() -> MultiTierLLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = MultiTierLLMService()
    return _llm_service


# Convenience function for quick chat
async def veena_chat(
    message: str,
    context: Optional[str] = None,
    history: Optional[List[ConversationMessage]] = None
) -> LLMResponse:
    """Quick chat with Veena"""
    service = get_llm_service()
    return await service.chat(message, history, context)
