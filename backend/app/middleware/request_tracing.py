"""Request tracing middleware and logging context."""

from __future__ import annotations

import logging
import re
import time
from uuid import uuid4

import sentry_sdk
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.tracing import (
    DEFAULT_TRACE_ID,
    SENTRY_TRACE_HEADER,
    TRACE_ID_HEADER,
    TRACEPARENT_HEADER,
    get_current_trace_id,
    reset_current_trace_id,
    set_current_trace_id,
)


_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
_TRACEPARENT_PATTERN = re.compile(r"^[0-9a-f]{2}-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$")
_SENTRY_TRACE_PATTERN = re.compile(r"^([0-9a-f]{32})-([0-9a-f]{16})(?:-[0-1])?$")
_trace_logging_configured = False


def configure_trace_logging() -> None:
    global _trace_logging_configured

    if _trace_logging_configured:
        return

    previous_factory = logging.getLogRecordFactory()

    def trace_aware_record_factory(*args, **kwargs):
        record = previous_factory(*args, **kwargs)
        record.trace_id = get_current_trace_id()
        return record

    logging.setLogRecordFactory(trace_aware_record_factory)
    _trace_logging_configured = True


def _normalize_trace_id(candidate: str | None) -> str | None:
    if not candidate:
        return None

    normalized = candidate.strip()
    if not normalized or not _TRACE_ID_PATTERN.fullmatch(normalized):
        return None

    return normalized


def _extract_trace_id(request: Request) -> str:
    sentry_trace = request.headers.get(SENTRY_TRACE_HEADER)
    if sentry_trace:
        sentry_match = _SENTRY_TRACE_PATTERN.fullmatch(sentry_trace.strip().lower())
        if sentry_match:
            return sentry_match.group(1)

    traceparent = request.headers.get(TRACEPARENT_HEADER)
    if traceparent:
        traceparent_match = _TRACEPARENT_PATTERN.fullmatch(traceparent.strip().lower())
        if traceparent_match:
            return traceparent_match.group(1)

    propagated_trace_id = _normalize_trace_id(request.headers.get(TRACE_ID_HEADER))
    if propagated_trace_id:
        return propagated_trace_id

    return uuid4().hex


def _bind_trace_context(request: Request, trace_id: str) -> None:
    request.state.trace_id = trace_id
    request.state.trace_started_at = time.perf_counter()
    sentry_sdk.set_tag("trace_id", trace_id)
    sentry_sdk.set_context(
        "request_trace",
        {
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
        },
    )


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Assigns and propagates a stable trace id for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = _extract_trace_id(request)
        trace_token = set_current_trace_id(trace_id)
        _bind_trace_context(request, trace_id)

        try:
            response = await call_next(request)
        finally:
            reset_current_trace_id(trace_token)

        response.headers[TRACE_ID_HEADER] = trace_id
        return response