"""Optional Mem0 platform adapter for developer-facing cloud memory.

This module keeps Mem0 separate from REEVU and exposes only a thin async
wrapper around Mem0's hosted platform client for developer or control-plane
memory workflows.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from time import perf_counter
from typing import Any

from app.core.config import settings


class Mem0ConfigurationError(RuntimeError):
    """Raised when Mem0 is enabled but required settings are incomplete."""


class Mem0DisabledError(RuntimeError):
    """Raised when callers try to use Mem0 while it is disabled."""


class Mem0Service:
    """Thin async wrapper around Mem0's hosted Memory client."""

    HEALTH_PROBE_QUERY = "__developer_mem0_health_probe__"

    def __init__(self, *, client_factory: Callable[..., Any] | None = None) -> None:
        self._client_factory = client_factory
        self._client: Any | None = None

    def is_enabled(self) -> bool:
        return settings.MEM0_ENABLED

    def is_configured(self) -> bool:
        return self.is_enabled() and bool(settings.MEM0_API_KEY)

    def status(self) -> dict[str, Any]:
        org_project_pair = bool(settings.MEM0_ORG_ID) == bool(settings.MEM0_PROJECT_ID)
        return {
            "enabled": self.is_enabled(),
            "configured": self.is_configured(),
            "host": settings.MEM0_HOST,
            "org_project_pair_valid": org_project_pair,
            "project_scoped": bool(settings.MEM0_ORG_ID and settings.MEM0_PROJECT_ID),
        }

    async def add_messages(
        self,
        messages: str | dict[str, str] | Sequence[dict[str, str]],
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        app_id: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()
        return await client.add(
            self._normalize_messages(messages),
            user_id=user_id,
            agent_id=agent_id,
            app_id=app_id,
            run_id=run_id,
            metadata=metadata,
        )

    async def search(
        self,
        query: str,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        app_id: str | None = None,
        run_id: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()
        return await client.search(
            query,
            user_id=user_id,
            agent_id=agent_id,
            app_id=app_id,
            run_id=run_id,
            top_k=limit,
            filters=filters,
        )

    async def health_check(
        self,
        *,
        user_id: str,
        agent_id: str,
        app_id: str,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()
        started_at = perf_counter()
        result = await client.search(
            self.HEALTH_PROBE_QUERY,
            user_id=user_id,
            agent_id=agent_id,
            app_id=app_id,
            run_id=run_id,
            top_k=1,
            filters=None,
        )
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        return {
            "reachable": True,
            "checked_at": datetime.now(UTC).isoformat(),
            "latency_ms": latency_ms,
            "result_count": self._count_results(result),
            "detail": "Mem0 cloud probe succeeded with the configured backend credentials.",
        }

    async def aclose(self) -> None:
        if self._client is None:
            return

        async_client = getattr(self._client, "async_client", None)
        if async_client is not None:
            await async_client.aclose()

        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        if not settings.MEM0_ENABLED:
            raise Mem0DisabledError(
                "Mem0 is disabled. Set MEM0_ENABLED=true before using the Mem0 service."
            )

        if not settings.MEM0_API_KEY:
            raise Mem0ConfigurationError(
                "Mem0 is enabled but MEM0_API_KEY is not configured."
            )

        if bool(settings.MEM0_ORG_ID) != bool(settings.MEM0_PROJECT_ID):
            raise Mem0ConfigurationError(
                "MEM0_ORG_ID and MEM0_PROJECT_ID must be configured together."
            )

        client_factory = self._client_factory
        if client_factory is None:
            from mem0 import AsyncMemoryClient

            client_factory = AsyncMemoryClient

        kwargs: dict[str, Any] = {
            "api_key": settings.MEM0_API_KEY,
            "host": settings.MEM0_HOST,
        }
        if settings.MEM0_ORG_ID and settings.MEM0_PROJECT_ID:
            kwargs["org_id"] = settings.MEM0_ORG_ID
            kwargs["project_id"] = settings.MEM0_PROJECT_ID

        return client_factory(**kwargs)

    def _normalize_messages(
        self,
        messages: str | dict[str, str] | Sequence[dict[str, str]],
    ) -> str | dict[str, str] | list[dict[str, str]]:
        if isinstance(messages, str):
            return messages
        if isinstance(messages, dict):
            return dict(messages)
        return [dict(message) for message in messages]

    def _count_results(self, payload: Any) -> int | None:
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return len(payload["results"])
        return None


@lru_cache(maxsize=1)
def get_mem0_service() -> Mem0Service:
    return Mem0Service()