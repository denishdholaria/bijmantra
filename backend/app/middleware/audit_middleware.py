"""Audit middleware with masking, lockdown and targeted rate limiting."""

from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.database import AsyncSessionLocal
from app.models.audit import AuditLog

SENSITIVE_KEYS = {"name", "full_name", "email", "phone", "contact", "address"}
HIGH_RESOURCE_SEGMENTS = {"/compute", "/gwas", "/mixed-model", "/simulation", "/biosimulation"}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class EmergencyLockdown:
    enabled: bool = False


class _SimpleLimiter:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._buckets[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True


high_resource_limiter = _SimpleLimiter()


def _mask_payload(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return payload
    masked = {}
    for key, value in payload.items():
        key_lower = str(key).lower()
        if any(s in key_lower for s in SENSITIVE_KEYS):
            masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = _mask_payload(value)
        else:
            masked[key] = value
    return masked


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs mutating requests on critical entities and enforces lockdown."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method.upper()

        if method in MUTATING_METHODS and EmergencyLockdown.enabled:
            return JSONResponse(status_code=423, content={"detail": "Emergency lockdown enabled"})

        if any(seg in path for seg in HIGH_RESOURCE_SEGMENTS):
            ip = self._client_ip(request)
            if not high_resource_limiter.allow(f"{ip}:{path}"):
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded for high-resource endpoint"})

        response = await call_next(request)

        if method in {"POST", "PUT", "DELETE"} and self._is_critical(path):
            user_id, org_id = self._user_and_org(request)
            log_payload = {
                "status_code": response.status_code,
                "query": dict(request.query_params),
            }
            asyncio.create_task(
                self._insert_log(
                    organization_id=org_id,
                    user_id=user_id,
                    action=method,
                    target_type=self._target_type(path),
                    target_id=self._target_id(path),
                    changes=_mask_payload(log_payload),
                    ip=self._client_ip(request),
                    request_path=path,
                    method=method,
                )
            )

        return response

    def _is_critical(self, path: str) -> bool:
        return any(token in path for token in ["/trials", "/germplasm", "/vision", "/sadhana"])

    def _target_type(self, path: str) -> str:
        for token in ["trials", "germplasm", "vision", "sadhana"]:
            if token in path:
                return token
        return "api"

    def _target_id(self, path: str) -> str | None:
        match = re.search(r"/(?:trials|germplasm|datasets|annotations)/([^/]+)", path)
        return match.group(1) if match else None

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _user_and_org(self, request: Request) -> tuple[int | None, int | None]:
        user = getattr(request.state, "user", None)
        if user is not None:
            return getattr(user, "id", None), getattr(user, "organization_id", None)
        return None, None

    async def _insert_log(self, **kwargs) -> None:
        async with AsyncSessionLocal() as db:
            db.add(AuditLog(**kwargs))
            await db.commit()
