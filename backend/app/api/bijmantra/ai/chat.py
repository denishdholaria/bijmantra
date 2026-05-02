"""REEVU Chat API — thin router. Business logic lives in app.services.chat.

Schema classes (ChatRequest, ChatResponse, ContextDocument, etc.) are defined
in app.schemas.chat and imported here. They must NOT be redefined in this file —
doing so creates a circular import with the service layer.
"""

import contextlib
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User
from app.modules.ai.service import get_ai_provider_service  # noqa: F401
from app.modules.ai.services.engine import (  # noqa: F401
    MultiTierLLMService,
    get_llm_service,
)
from app.modules.ai.services.memory import BreedingVectorService
from app.modules.ai.services.quota import AIQuotaService
from app.modules.ai.services.reevu import ReevuMetrics
from app.modules.ai.services.reevu_service import ReevuService, get_reevu_service
from app.modules.ai.services.tools import FunctionExecutor  # noqa: F401
from app.schemas.chat import (  # canonical schema location — no redefinition here
    ChatRequest,
    ChatResponse,
    ChatUsageResponse,
    ContextDocument,
    ContextRequest,
    ContextResponse,
)
from app.services.chat.context_service import ContextService
from app.services.chat.message_service import MessageService
from app.services.chat.orchestration_service import OrchestrationService
from app.services.chat.session_service import SessionService

# Legacy compatibility aliases — kept for test patch targets
from app.modules.ai.services.reevu_service import (  # noqa: F401
    ReevuService as VeenaService,
    get_reevu_service as get_veena_service,
)

logger = logging.getLogger(__name__)
REEVU_BENCHMARK_REPORT_PATH = (
    Path(__file__).resolve().parents[3] / "test_reports" / "reevu_real_question_local.json"
)

router = APIRouter(prefix="/chat", tags=["REEVU AI"], dependencies=[Depends(get_current_user)])

# Compatibility alias retained for tests and older patch targets.
_build_reevu_envelope = MessageService.build_reevu_envelope


# --- Dependencies ---

async def get_breeding_service(db: AsyncSession = Depends(get_tenant_db)) -> BreedingVectorService:
    return await SessionService.get_breeding_service(db)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _load_reevu_benchmark_status() -> dict[str, Any]:
    """Return a compact status view of the local REEVU benchmark artifact."""
    if not REEVU_BENCHMARK_REPORT_PATH.exists():
        return {
            "available": False,
            "runtime_status": "missing",
            "generated_at": None,
            "runtime_target": None,
            "runtime_path": "local",
            "local_organization_id": None,
            "passed_cases": 0,
            "failed_cases": 0,
            "total_cases": 0,
            "pass_rate": None,
            "readiness_blockers": [],
            "readiness_warnings": [],
        }

    try:
        payload = json.loads(REEVU_BENCHMARK_REPORT_PATH.read_text())
    except (OSError, ValueError) as exc:
        logger.warning("Failed to load REEVU benchmark artifact: %s", exc)
        return {
            "available": False,
            "runtime_status": "unreadable",
            "generated_at": None,
            "runtime_target": None,
            "runtime_path": "local",
            "local_organization_id": None,
            "passed_cases": 0,
            "failed_cases": 0,
            "total_cases": 0,
            "pass_rate": None,
            "readiness_blockers": [],
            "readiness_warnings": [],
        }

    if not isinstance(payload, dict):
        return {
            "available": False,
            "runtime_status": "invalid",
            "generated_at": None,
            "runtime_target": None,
            "runtime_path": "local",
            "local_organization_id": None,
            "passed_cases": 0,
            "failed_cases": 0,
            "total_cases": 0,
            "pass_rate": None,
            "readiness_blockers": [],
            "readiness_warnings": [],
        }

    passed_cases = int(payload.get("passed_cases") or 0)
    failed_cases = int(payload.get("failed_cases") or 0)
    total_cases = int(payload.get("total_cases") or (passed_cases + failed_cases))
    pass_rate = payload.get("pass_rate")

    return {
        "available": True,
        "runtime_status": str(payload.get("runtime_status") or "unknown"),
        "generated_at": payload.get("generated_at"),
        "runtime_target": payload.get("runtime_target"),
        "runtime_path": payload.get("runtime_path") or "local",
        "local_organization_id": payload.get("local_organization_id"),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "total_cases": total_cases,
        "pass_rate": float(pass_rate) if isinstance(pass_rate, (int, float)) else None,
        "readiness_blockers": _string_list(payload.get("readiness_blockers")),
        "readiness_warnings": _string_list(payload.get("readiness_warnings")),
    }


# --- Endpoints ---

@router.post("/", response_model=ChatResponse)
async def chat_with_reevu(
    request: ChatRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
    reevu_service: ReevuService = Depends(get_reevu_service),
):
    """Send a message to REEVU AI assistant."""
    return await OrchestrationService(db, current_user, reevu_service).handle_chat(request)


@router.post("/stream")
async def stream_chat_with_reevu(
    request: ChatRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
    reevu_service: ReevuService = Depends(get_reevu_service),
):
    """Stream a message to REEVU AI assistant (SSE)."""
    svc = OrchestrationService(db, current_user, reevu_service)
    return StreamingResponse(
        await svc.handle_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        },
    )


@router.post("/context", response_model=ContextResponse)
async def get_context(
    request: ContextRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_service),
):
    """Get relevant context documents for a query without generating a response."""
    docs = await ContextService.get_context_documents(
        breeding_service=breeding_service,
        query=request.query,
        doc_types=request.doc_types,
        limit=request.limit,
    )
    return ContextResponse(
        query=request.query,
        documents=[
            ContextDocument(
                doc_id=doc.doc_id, doc_type=doc.doc_type, title=doc.title,
                content=doc.content, similarity=doc.similarity, source_id=doc.source_id,
            )
            for doc in docs
        ],
        total=len(docs),
    )


@router.get("/status")
async def get_llm_status(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Get status of all LLM providers."""
    return await (await SessionService.get_request_llm_service(db, current_user)).get_status()


@router.get("/usage", response_model=ChatUsageResponse)
async def get_ai_usage(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Get daily AI usage statistics for the organization."""
    provider_status: dict[str, Any] | None = None
    with contextlib.suppress(Exception):
        provider_status = await (await SessionService.get_request_llm_service(db, current_user)).get_status()
    return await AIQuotaService.get_usage_stats(db, current_user.organization_id, provider_status=provider_status)


@router.get("/health")
async def reevu_health(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Check REEVU AI health status."""
    status = await (await SessionService.get_request_llm_service(db, current_user)).get_status()
    return {
        "status": "healthy",
        "assistant": "REEVU",
        "active_provider": status["active_provider"],
        "active_model": status["active_model"],
        "active_provider_source": status.get("active_provider_source", "none"),
        "active_provider_source_label": status.get("active_provider_source_label", "Unavailable"),
        "capabilities": [
            "semantic_search", "germplasm_lookup", "protocol_search",
            "trial_information", "similarity_matching", "natural_conversation",
        ],
        "rag_enabled": True,
        "llm_enabled": status["active_provider"] != "template",
        "free_tier_available": any(p["available"] and p["free_tier"] for p in status["providers"].values()),
    }


@router.get("/metrics")
async def reevu_metrics():
    """Return REEVU runtime metrics snapshot."""
    return ReevuMetrics.get().get_metrics_snapshot()


@router.get("/diagnostics")
async def reevu_diagnostics(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Return operator-facing REEVU diagnostics (superuser only)."""
    if not bool(getattr(current_user, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="Superuser access required")
    llm_service = await SessionService.get_request_llm_service(db, current_user)
    status = await llm_service.get_status()
    metrics_snapshot = ReevuMetrics.get().get_metrics_snapshot()
    diagnostics_snapshot = ReevuMetrics.get().get_diagnostics_snapshot()
    return {
        "assistant": "REEVU",
        "active_provider": status.get("active_provider", "unknown"),
        "active_model": status.get("active_model", "unknown"),
        "active_provider_source": status.get("active_provider_source", "none"),
        "active_provider_source_label": status.get("active_provider_source_label", "Unavailable"),
        "database_authority": SessionService.get_database_authority(),
        "uptime_seconds": metrics_snapshot.get("uptime_seconds", 0),
        "total_requests": metrics_snapshot.get("total_requests", 0),
        "providers": [
            {"provider": n, "available": s.get("available", False), "free_tier": s.get("free_tier", False)}
            for n, s in sorted(status.get("providers", {}).items())
        ],
        "routing_state": SessionService.get_llm_routing_state(llm_service),
        "request_statuses": diagnostics_snapshot.get("request_statuses", []),
        "provider_latencies": diagnostics_snapshot.get("provider_latencies", []),
        "safe_failures": diagnostics_snapshot.get("safe_failures", []),
        "routing_decisions": diagnostics_snapshot.get("routing_decisions", []),
        "retrieval_execution": diagnostics_snapshot.get("retrieval_execution", {}),
        "step_execution_traces": diagnostics_snapshot.get("step_execution_traces", {}),
        "narrowing_effectiveness": diagnostics_snapshot.get("narrowing_effectiveness", {}),
        "retrieval_outcomes": diagnostics_snapshot.get("retrieval_outcomes", []),
        "safe_failure_distribution": diagnostics_snapshot.get("safe_failure_distribution", []),
        "benchmark_status": _load_reevu_benchmark_status(),
        "policy_flags": metrics_snapshot.get("policy_flags", []),
    }


# Legacy compatibility aliases
chat_with_veena = chat_with_reevu
stream_chat_with_veena = stream_chat_with_reevu


async def veena_health():
    return await reevu_health()
