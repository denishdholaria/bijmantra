"""Base adapter contract for future provider extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


class IProviderAdapter(ABC):
    """Future provider adapter interface used by REEVU orchestration."""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return the provider handled by this adapter."""

    @abstractmethod
    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        """Execute a non-streaming provider call."""

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming provider call."""