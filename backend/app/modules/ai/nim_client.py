"""Standalone NVIDIA NIM client utility.

Provides a thin, dependency-minimal wrapper around the OpenAI-compatible NIM
endpoint so callers (scripts, tests, non-REEVU paths) can make chat requests
without wiring up the full REEVU engine stack.

Usage::

    from app.modules.ai.nim_client import NimClient

    client = NimClient()  # reads env vars automatically
    response = await client.chat([{"role": "user", "content": "Hello"}])
    print(response)

    # Streaming
    async for chunk in client.stream([{"role": "user", "content": "Hello"}]):
        print(chunk, end="", flush=True)

Environment variables:
    NVIDIA_API_KEY  – required; NIM bearer token
    NIM_MODEL       – model name (default: meta/llama-3.1-70b-instruct)
    NIM_BASE_URL    – endpoint (default: https://integrate.api.nvidia.com/v1)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import NamedTuple

import httpx


logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"
_DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
_RETRY_BACKOFF_SECONDS = 2.0
_MAX_RETRIES = 1


class NimChatResult(NamedTuple):
    content: str
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: float


class NimClient:
    """Minimal async NIM client (OpenAI-compatible /chat/completions)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.model = model or os.environ.get("NIM_MODEL", _DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get("NIM_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

        if not self.api_key:
            logger.warning("[NIM] NVIDIA_API_KEY is not set; calls will fail with 401")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> NimChatResult:
        """Send a blocking chat request and return the full response.

        Retries once on HTTP 429 with a short backoff.
        """
        target_model = model or self.model
        client = await self._get_http_client()
        attempt = 0

        while True:
            t0 = time.monotonic()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": target_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            latency_ms = (time.monotonic() - t0) * 1000

            if response.status_code == 429 and attempt < _MAX_RETRIES:
                attempt += 1
                logger.warning("[NIM] 429 rate-limited; retrying in %.1fs", _RETRY_BACKOFF_SECONDS)
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                continue

            response.raise_for_status()
            data = response.json()
            usage = data.get("usage", {})
            content = data["choices"][0]["message"]["content"].strip()
            logger.debug("[NIM] chat latency=%.1f ms model=%s", latency_ms, data.get("model"))
            return NimChatResult(
                content=content,
                model=data.get("model"),
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                latency_ms=latency_ms,
            )

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Yield token chunks from a streaming NIM chat request."""
        target_model = model or self.model
        client = await self._get_http_client()
        attempt = 0
        t0 = time.monotonic()

        while True:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": target_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                if response.status_code == 429 and attempt < _MAX_RETRIES:
                    attempt += 1
                    logger.warning("[NIM] 429 rate-limited (stream); retrying in %.1fs", _RETRY_BACKOFF_SECONDS)
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                    continue

                response.raise_for_status()
                first_token = True
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            elapsed = (time.monotonic() - t0) * 1000
                            logger.debug("[NIM] stream complete latency=%.1f ms", elapsed)
                            return
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                if first_token:
                                    ttft = (time.monotonic() - t0) * 1000
                                    logger.debug("[NIM] time-to-first-token=%.1f ms", ttft)
                                    first_token = False
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
            return  # clean exit

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "NimClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
