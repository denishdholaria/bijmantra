"""Ollama provider adapter using the OpenAI-compatible chat interface."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


def _ollama_chat_completions_url(base_url: str | None) -> str | None:
	if not base_url:
		return None

	normalized = base_url.rstrip("/")
	if normalized.endswith("/v1"):
		return f"{normalized}/chat/completions"

	return f"{normalized}/v1/chat/completions"


class OllamaAdapter(IProviderAdapter):
	def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
		self._get_client = get_client

	@property
	def provider(self) -> LLMProvider:
		return LLMProvider.OLLAMA

	async def call(
		self,
		messages: list[dict[str, str]],
		config: LLMConfig,
	) -> LLMCallResult | None:
		url = _ollama_chat_completions_url(config.base_url)
		if not url:
			return None

		try:
			client = await self._get_client()
			headers = {"Content-Type": "application/json"}
			if config.api_key:
				headers["Authorization"] = f"Bearer {config.api_key}"

			response = await client.post(
				url,
				headers=headers,
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
		except Exception as exc:
			logger.error("[Veena] Ollama error: %s", exc)
		return None

	async def stream(
		self,
		messages: list[dict[str, str]],
		config: LLMConfig,
	) -> AsyncGenerator[str, None]:
		url = _ollama_chat_completions_url(config.base_url)
		if not url:
			return

		try:
			client = await self._get_client()
			headers = {"Content-Type": "application/json"}
			if config.api_key:
				headers["Authorization"] = f"Bearer {config.api_key}"

			async with client.stream(
				"POST",
				url,
				headers=headers,
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
		except Exception as exc:
			logger.error("[Veena] Ollama streaming error: %s", exc)
			yield f"[Error: {str(exc)}]"