"""Shared provider types for REEVU LLM infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LLMProvider(StrEnum):
    """Available local and cloud LLM providers."""

    OLLAMA = "ollama"
    GROQ = "groq"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    FUNCTIONGEMMA = "functiongemma"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TEMPLATE = "template"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    provider: LLMProvider
    model: str
    source: str = "server_env"
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.7
    available: bool = False
    free_tier: bool = True
    rate_limit: int | None = None


@dataclass
class LLMCallResult:
    """Result from a single LLM API call (internal use)."""

    content: str
    model_from_response: str | None = None
    tokens_used: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None