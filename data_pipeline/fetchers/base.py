from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from data_pipeline.io import ensure_dirs, read_json, utc_now_iso, write_json


CACHE_TTL_DAYS = 7


@dataclass(slots=True)
class FetchResult:
    source: str
    ok: bool
    record_count: int
    raw_path: Path
    error: str | None = None


class BaseFetcher:
    source_name = "base"

    def __init__(self, raw_dir: Path, timeout_seconds: float = 20.0):
        self.raw_dir = raw_dir
        self.timeout_seconds = timeout_seconds

    async def fetch(self, **params: Any) -> FetchResult:
        raise NotImplementedError

    def _cache_result(self, name: str, *, force_fetch: bool = False) -> FetchResult | None:
        raw_path = self.raw_dir / f"{name}.json"
        if force_fetch or not raw_path.exists() or not self._is_cache_fresh(raw_path):
            return None
        payload = read_json(raw_path, default={})
        return FetchResult(
            source=self.source_name,
            ok=True,
            record_count=_payload_count(payload.get("data") if isinstance(payload, dict) else payload),
            raw_path=raw_path,
        )

    def _is_cache_fresh(self, raw_path: Path) -> bool:
        age = datetime.now(UTC) - datetime.fromtimestamp(raw_path.stat().st_mtime, UTC)
        return age < timedelta(days=CACHE_TTL_DAYS)

    def _write_payload(self, name: str, payload: Any, metadata: dict[str, Any]) -> FetchResult:
        ensure_dirs(self.raw_dir)
        raw_path = self.raw_dir / f"{name}.json"
        write_json(
            raw_path,
            {
                "metadata": {
                    "source": self.source_name,
                    "fetched_at": utc_now_iso(),
                    **metadata,
                },
                "data": payload,
            },
        )
        count = _payload_count(payload)
        return FetchResult(source=self.source_name, ok=True, record_count=count, raw_path=raw_path)

    def _write_error(self, name: str, exc: Exception) -> FetchResult:
        ensure_dirs(self.raw_dir)
        raw_path = self.raw_dir / f"{name}_error.json"
        write_json(
            raw_path,
            {
                "metadata": {
                    "source": self.source_name,
                    "fetched_at": utc_now_iso(),
                    "ok": False,
                },
                "source": self.source_name,
                "ok": False,
                "error": str(exc),
            },
        )
        return FetchResult(source=self.source_name, ok=False, record_count=0, raw_path=raw_path, error=str(exc))

    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        try:
            import httpx
            from tenacity import retry, stop_after_attempt, wait_exponential
        except ImportError as exc:
            raise RuntimeError(
                "Fetchers require backend uv dependencies. Run from backend with "
                "`PYTHONPATH=.. uv run python -m data_pipeline fetch`."
            ) from exc

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
        async def request_json() -> Any:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        return await request_json()


def _payload_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        data = payload.get("result", {}).get("data") if isinstance(payload.get("result"), dict) else None
        if isinstance(data, list):
            return len(data)
        rows = payload.get("data")
        if isinstance(rows, list):
            return len(rows)
    return 1 if payload is not None else 0
