from __future__ import annotations

import httpx
import pytest

from app.core.http_tracing import create_traced_async_client, merge_trace_headers
from app.core.tracing import TRACE_ID_HEADER, trace_context


@pytest.mark.asyncio
async def test_traced_async_client_propagates_current_trace_id():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with create_traced_async_client(
        base_url="http://trace.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        with trace_context("backend-httpx-trace-1234"):
            response = await client.get("/health")

    assert response.status_code == 200
    assert captured_requests[0].headers.get(TRACE_ID_HEADER) == "backend-httpx-trace-1234"


@pytest.mark.asyncio
async def test_traced_async_client_preserves_explicit_trace_id_header():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with create_traced_async_client(
        base_url="http://trace.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        with trace_context("backend-httpx-trace-1234"):
            response = await client.get(
                "/health",
                headers={TRACE_ID_HEADER: "explicit-backend-trace-5678"},
            )

    assert response.status_code == 200
    assert captured_requests[0].headers.get(TRACE_ID_HEADER) == "explicit-backend-trace-5678"


def test_merge_trace_headers_uses_current_trace_context():
    with trace_context("merged-backend-trace-9999"):
        headers = merge_trace_headers({"Accept": "application/json"})

    assert headers == {
        "Accept": "application/json",
        TRACE_ID_HEADER: "merged-backend-trace-9999",
    }