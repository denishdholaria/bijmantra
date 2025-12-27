"""
Multi-Tier LLM Service for Veena AI

Designed for accessibility - works for students in developing countries
who cannot afford API keys.

Tiers (in order of preference):
1. LOCAL: Ollama (free, private, works offline)
2. FREE CLOUD: Groq, Google AI Studio, HuggingFace (free tiers)
3. PAID: OpenAI, Anthropic (for institutions with budget)
4. FALLBACK: Enhanced template responses

Configuration via environment variables:
- OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
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
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"           # Local, free, private
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
class LLMResponse:
    """Response from LLM"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: Optional[int] = None
    cached: bool = False
    latency_ms: Optional[float] = None


@dataclass
class ConversationMessage:
    """A message in conversation history"""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


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
    
    # Breeding-focused system prompt
    SYSTEM_PROMPT = """You are Veena (वीणा), an intelligent AI assistant for plant breeding and agricultural research.

Your name comes from the sacred instrument of Goddess Saraswati, symbolizing wisdom and knowledge.

You help researchers and students with:
- Plant breeding concepts and methodologies
- Germplasm management and characterization
- Trial design and analysis
- Genomics and marker-assisted selection
- Crop improvement strategies
- Statistical analysis for breeding
- Seed production and quality

Guidelines:
- Be helpful, accurate, and educational
- Explain complex concepts simply when needed
- Cite sources when providing specific data
- Acknowledge uncertainty when appropriate
- Be encouraging to students learning breeding
- Use examples from real crops when helpful

If you receive context from the knowledge base, use it to provide accurate, specific answers.
If no context is provided, use your general knowledge but note when information might need verification."""

    def __init__(self):
        self.providers: Dict[LLMProvider, LLMConfig] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers"""
        
        # 1. Ollama (Local, Free)
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.providers[LLMProvider.OLLAMA] = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=ollama_host,
            free_tier=True,
            rate_limit=None  # No limit for local
        )
        
        # 2. Groq (Free tier: 30 req/min)
        groq_key = os.getenv("GROQ_API_KEY")
        self.providers[LLMProvider.GROQ] = LLMConfig(
            provider=LLMProvider.GROQ,
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            available=bool(groq_key),
            free_tier=True,
            rate_limit=30
        )
        
        # 3. Google AI Studio (Free tier: 60 req/min)
        google_key = os.getenv("GOOGLE_AI_KEY")
        self.providers[LLMProvider.GOOGLE] = LLMConfig(
            provider=LLMProvider.GOOGLE,
            model=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
            api_key=google_key,
            base_url="https://generativelanguage.googleapis.com/v1beta",
            available=bool(google_key),
            free_tier=True,
            rate_limit=60
        )
        
        # 4. HuggingFace (Free tier)
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        self.providers[LLMProvider.HUGGINGFACE] = LLMConfig(
            provider=LLMProvider.HUGGINGFACE,
            model=os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
            api_key=hf_key,
            base_url="https://api-inference.huggingface.co/models",
            available=bool(hf_key),
            free_tier=True,
            rate_limit=10
        )
        
        # 5. FunctionGemma (Function calling, 270M)
        # Can use same HuggingFace key or separate
        functiongemma_key = os.getenv("FUNCTIONGEMMA_API_KEY") or hf_key
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
        openai_key = os.getenv("OPENAI_API_KEY")
        self.providers[LLMProvider.OPENAI] = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=openai_key,
            base_url="https://api.openai.com/v1",
            available=bool(openai_key),
            free_tier=False,
            rate_limit=60
        )
        
        # 7. Anthropic (Paid)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.providers[LLMProvider.ANTHROPIC] = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
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
    
    async def check_ollama_available(self) -> bool:
        """Check if Ollama is running and has models"""
        try:
            client = await self._get_client()
            config = self.providers[LLMProvider.OLLAMA]
            response = await client.get(f"{config.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check if our preferred model or any model is available
                if models:
                    config.available = True
                    # Use first available model if preferred not found
                    if config.model not in models and not any(config.model in m for m in models):
                        config.model = models[0]
                    logger.info(f"[Veena] Ollama available with models: {models}")
                    return True
        except Exception as e:
            logger.debug(f"[Veena] Ollama not available: {e}")
        return False
    
    async def get_available_providers(self) -> List[LLMConfig]:
        """Get list of available providers in priority order"""
        # Check Ollama availability (async check)
        await self.check_ollama_available()
        
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
        
        # Return available providers in priority order
        priority_order = [
            LLMProvider.OLLAMA,      # Local first
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


    async def _call_ollama(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
        """Call Ollama API"""
        try:
            client = await self._get_client()
            
            # Convert to Ollama format
            prompt = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"
            prompt += "Assistant: "
            
            response = await client.post(
                f"{config.base_url}/api/generate",
                json={
                    "model": config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.temperature,
                        "num_predict": config.max_tokens,
                    }
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"[Veena] Ollama error: {e}")
        return None
    
    async def _call_groq(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
        """Call Groq API (OpenAI-compatible)"""
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
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"[Veena] Groq error: {e}")
        return None
    
    async def _call_google(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
        """Call Google AI Studio API"""
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
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            logger.error(f"[Veena] Google AI error: {e}")
        return None
    
    async def _call_huggingface(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
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
                    return data[0].get("generated_text", "").strip()
        except Exception as e:
            logger.error(f"[Veena] HuggingFace error: {e}")
        return None
    
    async def _call_openai(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
        """Call OpenAI API"""
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
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"[Veena] OpenAI error: {e}")
        return None
    
    async def _call_anthropic(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig
    ) -> Optional[str]:
        """Call Anthropic API"""
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
                content = data.get("content", [])
                if content:
                    return content[0].get("text", "").strip()
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
                if datetime.utcnow() - timestamp < CACHE_TTL:
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
            
            content = None
            try:
                if config.provider == LLMProvider.OLLAMA:
                    content = await self._call_ollama(messages, config)
                elif config.provider == LLMProvider.GROQ:
                    content = await self._call_groq(messages, config)
                elif config.provider == LLMProvider.GOOGLE:
                    content = await self._call_google(messages, config)
                elif config.provider == LLMProvider.HUGGINGFACE:
                    content = await self._call_huggingface(messages, config)
                elif config.provider == LLMProvider.OPENAI:
                    content = await self._call_openai(messages, config)
                elif config.provider == LLMProvider.ANTHROPIC:
                    content = await self._call_anthropic(messages, config)
                
                if content:
                    latency = (time.time() - start_time) * 1000
                    response = LLMResponse(
                        content=content,
                        provider=config.provider,
                        model=config.model,
                        latency_ms=latency
                    )
                    
                    # Cache the response
                    if use_cache:
                        _response_cache[cache_key] = (response, datetime.utcnow())
                    
                    logger.info(f"[Veena] Response from {config.provider.value} in {latency:.0f}ms")
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
            latency_ms=(time.time() - start_time) * 1000
        )
    
    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        context: Optional[str] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        High-level chat interface for Veena.
        
        Args:
            user_message: The user's message
            conversation_history: Previous messages in conversation
            context: RAG context to include
            use_cache: Whether to cache responses
        
        Returns:
            LLMResponse
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
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
        
        return await self.generate(messages, use_cache=use_cache)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers"""
        available = await self.get_available_providers()
        
        status = {
            "active_provider": available[0].provider.value if available else "none",
            "active_model": available[0].model if available else "none",
            "providers": {}
        }
        
        for provider, config in self.providers.items():
            status["providers"][provider.value] = {
                "available": config.available,
                "model": config.model,
                "free_tier": config.free_tier,
                "rate_limit": config.rate_limit,
                "configured": bool(config.api_key) or provider in [LLMProvider.OLLAMA, LLMProvider.TEMPLATE]
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
