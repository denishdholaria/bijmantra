"""
Streaming service for REEVU chat.

Handles SSE event construction and streaming-specific orchestration helpers.
Extracted from backend/app/api/v2/chat.py.
"""

import json
import logging
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from app.modules.ai.services.reevu import ReevuStage

logger = logging.getLogger(__name__)


class StreamingService:
    """Service for SSE event construction and streaming orchestration."""

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self._stage_started_at: dict[str, float] = {}

    # ------------------------------------------------------------------ #
    # SSE event builders                                                   #
    # ------------------------------------------------------------------ #

    def stage_event(self, stage: ReevuStage, status: str, **extra: Any) -> str:
        """Build a stage-lifecycle SSE event string."""
        stage_key = stage.value
        now_perf = perf_counter()
        payload: dict[str, Any] = {
            "type": "stage",
            "request_id": self.request_id,
            "stage": stage_key,
            "status": status,
            "ts": datetime.now(UTC).isoformat(),
        }

        if status == "started":
            self._stage_started_at[stage_key] = now_perf
        elif status == "completed":
            started_at = self._stage_started_at.get(stage_key)
            payload["latency_ms"] = (
                round((now_perf - started_at) * 1000, 3) if started_at is not None else 0.0
            )

        payload.update(extra)
        return f"data: {json.dumps(payload)}\n\n"

    def run_event(self, event: str, status: str, **extra: Any) -> str:
        """Build a first-class REEVU run timeline SSE event string."""
        payload: dict[str, Any] = {
            "type": "reevu_run",
            "request_id": self.request_id,
            "run_id": self.request_id,
            "event_id": f"{self.request_id}:{event}:{datetime.now(UTC).timestamp()}",
            "event": event,
            "status": status,
            "ts": datetime.now(UTC).isoformat(),
        }
        payload.update(extra)
        return f"data: {json.dumps(payload)}\n\n"

    def chunk_event(self, content: str) -> str:
        """Build a text-chunk SSE event string."""
        return f"data: {json.dumps({'type': 'chunk', 'request_id': self.request_id, 'content': content})}\n\n"

    def start_event(self, provider: str, model: str) -> str:
        """Build the stream-start SSE event string."""
        return f"data: {json.dumps({'type': 'start', 'request_id': self.request_id, 'provider': provider, 'model': model})}\n\n"

    def done_event(self) -> str:
        """Build the stream-done SSE event string."""
        return f"data: {json.dumps({'type': 'done', 'request_id': self.request_id})}\n\n"

    def error_event(self, message: str, safe_failure: dict[str, Any] | None = None) -> str:
        """Build an error SSE event string."""
        payload: dict[str, Any] = {
            "type": "error",
            "message": message,
            "request_id": self.request_id,
        }
        if safe_failure is not None:
            payload["safe_failure"] = safe_failure
        return f"data: {json.dumps(payload)}\n\n"

    def summary_event(self, payload: dict[str, Any]) -> str:
        """Build a summary SSE event string."""
        payload = {"type": "summary", "request_id": self.request_id, **payload}
        return f"data: {json.dumps(payload)}\n\n"

    def proposal_event(self, proposal_data: dict[str, Any]) -> str:
        """Build a proposal-created SSE event string."""
        return f"data: {json.dumps({'type': 'proposal_created', 'data': proposal_data})}\n\n"

    @staticmethod
    def keepalive() -> str:
        """Return an SSE keepalive comment."""
        return ": keepalive\n\n"

    # ------------------------------------------------------------------ #
    # Template-mode guard                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_template_only_mode(status: dict[str, Any]) -> bool:
        """Return True when the LLM service is in template-only fallback mode."""
        return status.get("active_provider") == "template" and not any(
            p.get("available") for p in status.get("providers", {}).values()
        )

    def template_mode_events(self) -> list[str]:
        """Yield the SSE events emitted when running in template-only mode."""
        return [
            self.chunk_event("I'm running in template mode without an AI backend. "),
            self.chunk_event("Please configure an AI provider for full features."),
            self.done_event(),
        ]
