"""Helpers for propagating the current trace id through outbound httpx clients."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import httpx

from app.core.tracing import DEFAULT_TRACE_ID, TRACE_ID_HEADER, get_current_trace_id


async def _inject_trace_id_header(request: httpx.Request) -> None:
    trace_id = get_current_trace_id()
    if trace_id == DEFAULT_TRACE_ID or request.headers.get(TRACE_ID_HEADER):
        return

    request.headers[TRACE_ID_HEADER] = trace_id


def merge_trace_headers(headers: Mapping[str, str] | None = None) -> dict[str, str]:
    merged_headers = dict(headers or {})
    trace_id = get_current_trace_id()

    if trace_id != DEFAULT_TRACE_ID and TRACE_ID_HEADER not in merged_headers:
        merged_headers[TRACE_ID_HEADER] = trace_id

    return merged_headers


def build_traced_event_hooks(
    event_hooks: Mapping[str, list[Callable[..., Any]]] | None = None,
) -> dict[str, list[Callable[..., Any]]]:
    merged_hooks = {name: list(hooks) for name, hooks in (event_hooks or {}).items()}
    request_hooks = merged_hooks.setdefault("request", [])

    if _inject_trace_id_header not in request_hooks:
        request_hooks.append(_inject_trace_id_header)

    return merged_hooks


def create_traced_async_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
    kwargs["event_hooks"] = build_traced_event_hooks(kwargs.get("event_hooks"))
    return httpx.AsyncClient(*args, **kwargs)