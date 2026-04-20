"""HuggingFace provider adapter."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class HuggingFaceAdapter(IProviderAdapter):
    def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
        self._get_client = get_client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.HUGGINGFACE

    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        try:
            client = await self._get_client()
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
                    },
                },
                timeout=120.0,
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    content = data[0].get("generated_text", "").strip()
                    return LLMCallResult(content=content)
        except Exception as e:
            logger.error("[REEVU] HuggingFace error: %s", e)
        return None

    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError("HuggingFace streaming is not currently supported")