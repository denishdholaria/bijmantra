"""Shared trace context utilities for backend request and client propagation."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Final


TRACE_ID_HEADER: Final = "X-Trace-Id"
TRACEPARENT_HEADER: Final = "traceparent"
SENTRY_TRACE_HEADER: Final = "sentry-trace"
DEFAULT_TRACE_ID: Final = "-"

_current_trace_id: ContextVar[str] = ContextVar("current_trace_id", default=DEFAULT_TRACE_ID)


def get_current_trace_id() -> str:
    return _current_trace_id.get()


def set_current_trace_id(trace_id: str) -> Token[str]:
    return _current_trace_id.set(trace_id)


def reset_current_trace_id(token: Token[str]) -> None:
    _current_trace_id.reset(token)


@contextmanager
def trace_context(trace_id: str):
    token = set_current_trace_id(trace_id)
    try:
        yield trace_id
    finally:
        reset_current_trace_id(token)