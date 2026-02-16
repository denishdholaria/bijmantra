"""Development-only route profiler middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("route_profiler")


class RouteProfilerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info("[RouteProfiler] %s %s -> %s in %.2fms", request.method, request.url.path, response.status_code, duration_ms)
        return response
