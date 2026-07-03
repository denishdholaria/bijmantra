"""NVIDIA NIM proxy endpoint.

Exposes POST /api/v2/nim/chat so the React frontend can call NIM without
holding the NVIDIA_API_KEY in the browser.

Security: NVIDIA_API_KEY is read from server-side settings only.
          This route requires a valid user session (get_current_user dep).

Endpoints:
    POST /nim/chat          – blocking response
    POST /nim/chat?stream=true – SSE streaming response
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.bijmantra.dependencies import get_current_user
from app.modules.ai.nim_client import NimClient


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nim", tags=["NVIDIA NIM"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class NimMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class NimChatRequest(BaseModel):
    messages: list[NimMessage]
    model: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=32768)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False


class NimChatResponse(BaseModel):
    content: str
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: float


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    response_model=NimChatResponse,
    summary="NVIDIA NIM chat proxy",
    description=(
        "Server-side proxy to NVIDIA NIM. "
        "Requires NVIDIA_API_KEY to be configured on the server; "
        "the key is never exposed to the frontend. "
        "Pass `?stream=true` or set `stream: true` in the body for SSE streaming."
    ),
)
async def nim_chat(
    body: NimChatRequest,
    stream: bool = Query(default=False, description="Enable SSE streaming"),
    _current_user: Any = Depends(get_current_user),
) -> NimChatResponse | StreamingResponse:
    from app.core.config import settings

    api_key = settings.NVIDIA_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NVIDIA NIM is not configured on this server (NVIDIA_API_KEY missing).",
        )

    messages = [m.model_dump() for m in body.messages]
    use_stream = stream or body.stream

    client = NimClient(
        api_key=api_key,
        model=body.model or settings.NIM_MODEL,
        base_url=settings.NIM_BASE_URL,
    )

    if use_stream:
        return StreamingResponse(
            _stream_generator(client, messages, body),
            media_type="text/event-stream",
        )

    try:
        result = await client.chat(
            messages,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
    except Exception as exc:
        logger.error("[NIM proxy] call failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"NIM request failed: {exc}",
        ) from exc
    finally:
        await client.aclose()

    return NimChatResponse(
        content=result.content,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        latency_ms=result.latency_ms,
    )


async def _stream_generator(
    client: NimClient,
    messages: list[dict],
    body: NimChatRequest,
):
    """Yield SSE-formatted chunks, then close the client."""
    try:
        async for chunk in client.stream(
            messages,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        ):
            payload = json.dumps({"chunk": chunk})
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        logger.error("[NIM proxy] stream failed: %s", exc)
        error_payload = json.dumps({"error": str(exc)})
        yield f"data: {error_payload}\n\n"
    finally:
        await client.aclose()
