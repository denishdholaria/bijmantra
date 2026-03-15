"""Groq provider adapter."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class GroqAdapter(IProviderAdapter):
    def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
        self._get_client = get_client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GROQ

    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        try:
            client = await self._get_client()
            response = await client.post(
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                },
            )

            if response.status_code == 200:
                data = response.json()
                model_from_response = data.get("model")
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                content = data["choices"][0]["message"]["content"].strip()
                return LLMCallResult(
                    content=content,
                    model_from_response=model_from_response,
                    tokens_used=tokens_used,
                )
        except Exception as e:
            logger.error("[Veena] Groq error: %s", e)
        return None

    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._get_client()
            async with client.stream(
                "POST",
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "stream": True,
                },
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
            logger.error("[Veena] Groq streaming error: %s", e)
            yield f"[Error: {str(e)}]"