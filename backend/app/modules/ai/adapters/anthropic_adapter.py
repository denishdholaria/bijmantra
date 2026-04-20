"""Anthropic provider adapter."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class AnthropicAdapter(IProviderAdapter):
    def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
        self._get_client = get_client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC

    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        try:
            client = await self._get_client()
            system = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    chat_messages.append(msg)

            body: dict[str, object] = {
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
                    "Content-Type": "application/json",
                },
                json=body,
            )

            if response.status_code == 200:
                data = response.json()
                model_from_response = data.get("model")
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                tokens_used = (input_tokens or 0) + (output_tokens or 0)
                content_list = data.get("content", [])
                if content_list:
                    content = content_list[0].get("text", "").strip()
                    return LLMCallResult(
                        content=content,
                        model_from_response=model_from_response,
                        tokens_used=tokens_used if tokens_used else None,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
        except Exception as e:
            logger.error("[REEVU] Anthropic error: %s", e)
        return None

    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._get_client()
            system = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    chat_messages.append(msg)

            body: dict[str, object] = {
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
                    "Content-Type": "application/json",
                },
                json=body,
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
            logger.error("[REEVU] Anthropic streaming error: %s", e)
            yield f"[Error: {str(e)}]"