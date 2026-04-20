"""Google provider adapter."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.modules.ai.adapters.base import IProviderAdapter
from app.modules.ai.services.provider_types import LLMCallResult, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class GoogleAdapter(IProviderAdapter):
    def __init__(self, get_client: Callable[[], Awaitable[object]]) -> None:
        self._get_client = get_client

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE

    async def call(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> LLMCallResult | None:
        try:
            client = await self._get_client()
            contents: list[dict[str, object]] = []
            system_instruction = None

            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}],
                    })

            body: dict[str, object] = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": config.max_tokens,
                    "temperature": config.temperature,
                },
            }
            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            response = await client.post(
                f"{config.base_url}/models/{config.model}:generateContent?key={config.api_key}",
                json=body,
            )

            if response.status_code == 200:
                data = response.json()
                model_from_response = data.get("modelVersion") or data.get("model")
                usage = data.get("usageMetadata", {})
                tokens_used = usage.get("totalTokenCount")
                input_tokens = usage.get("promptTokenCount")
                output_tokens = usage.get("candidatesTokenCount")
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "").strip()
                        return LLMCallResult(
                            content=content,
                            model_from_response=model_from_response,
                            tokens_used=tokens_used,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )
        except Exception as e:
            logger.error("[REEVU] Google AI error: %s", e)
        return None

    async def stream(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._get_client()
            contents: list[dict[str, object]] = []
            system_instruction = None

            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}],
                    })

            body: dict[str, object] = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": config.max_tokens,
                    "temperature": config.temperature,
                },
            }

            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            async with client.stream(
                "POST",
                f"{config.base_url}/models/{config.model}:streamGenerateContent?alt=sse&key={config.api_key}",
                json=body,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error("[REEVU] Google API error %s: %s", response.status_code, error_text)
                    yield f"[API Error: {response.status_code}]"
                    return

                async for line in response.aiter_lines():
                    if line:
                        try:
                            line = line.strip()
                            if line.startswith('data: '):
                                line = line[6:]

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

                            if "error" in data:
                                error_msg = data["error"].get("message", "Unknown error")
                                logger.error("[REEVU] Google API returned error: %s", error_msg)
                                yield f"[Error: {error_msg}]"
                                return
                        except json.JSONDecodeError:
                            logger.debug("[REEVU] Skipping non-JSON line: %s", line[:100])
                            continue
        except Exception as e:
            logger.error("[REEVU] Google streaming error: %s", e)
            yield f"[Error: {str(e)}]"