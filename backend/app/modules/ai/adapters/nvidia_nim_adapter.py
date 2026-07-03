"""NVIDIA NIM provider adapter.

NIM exposes an OpenAI-compatible /chat/completions endpoint at
https://integrate.api.nvidia.com/v1 — this adapter reuses the same
streaming and non-streaming logic as the OpenAI adapter but targets the
NIM base URL and uses the NVIDIA_API_KEY credential.

Retry behaviour: a single automatic retry with 2-second backoff on HTTP 429
(rate-limited) responses before bubbling the error to the caller.
Latency is logged at DEBUG level for every request.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)

_MAX_RETRIES = 1
_RETRY_BACKOFF_SECONDS = 2.0


class NvidiaNimAdapter(IProviderAdapter):
    """Adapter for NVIDIA NIM (OpenAI-compatible chat completions endpoint)."""

    def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
        self._get_client = get_client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.NVIDIA_NIM

    # ------------------------------------------------------------------
    # Non-streaming call
    # ------------------------------------------------------------------

    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        attempt = 0
        while True:
            try:
                client = await self._get_client()
                t0 = time.monotonic()
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
                elapsed_ms = (time.monotonic() - t0) * 1000
                logger.debug("[NIM] call latency=%.1f ms status=%s", elapsed_ms, response.status_code)

                if response.status_code == 429 and attempt < _MAX_RETRIES:
                    attempt += 1
                    logger.warning("[NIM] 429 rate-limited; retrying in %.1fs (attempt %d)", _RETRY_BACKOFF_SECONDS, attempt)
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    usage = data.get("usage", {})
                    content = data["choices"][0]["message"]["content"].strip()
                    return LLMCallResult(
                        content=content,
                        model_from_response=data.get("model"),
                        tokens_used=usage.get("total_tokens"),
                        input_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                    )

                logger.error("[NIM] Unexpected status %s: %s", response.status_code, response.text[:200])
                return None

            except Exception as e:
                logger.error("[NIM] call error: %s", e)
                raise

    # ------------------------------------------------------------------
    # Streaming call
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        attempt = 0
        while True:
            try:
                client = await self._get_client()
                t0 = time.monotonic()
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
                    if response.status_code == 429 and attempt < _MAX_RETRIES:
                        attempt += 1
                        logger.warning("[NIM] 429 rate-limited (stream); retrying in %.1fs", _RETRY_BACKOFF_SECONDS)
                        await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                        continue

                    first_token = True
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                elapsed_ms = (time.monotonic() - t0) * 1000
                                logger.debug("[NIM] stream complete latency=%.1f ms", elapsed_ms)
                                return
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    if first_token:
                                        ttft_ms = (time.monotonic() - t0) * 1000
                                        logger.debug("[NIM] time-to-first-token=%.1f ms", ttft_ms)
                                        first_token = False
                                    yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                return  # clean exit after inner async-with

            except Exception as e:
                logger.error("[NIM] stream error: %s", e)
                yield f"[Error: {e!s}]"
                return
